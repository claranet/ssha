from __future__ import unicode_literals

import copy
import os
import re
import subprocess
import tempfile

from fnmatch import fnmatch
from paramiko.config import SSHConfig

from . import errors, settings

try:
    basestring
except NameError:
    basestring = str


_config = {}
_ssh_config = {}
_tempfiles = {}


def _exec(command):
    return subprocess.check_output(command, shell=True).strip().decode('utf-8')


def _get(key, default=None):
    value = _config
    for key in key.split('.'):
        value = value.get(key)
        if not value:
            break
    return value or default


def _get_ssh_config(key):
    if not _ssh_config:

        ssh_config = SSHConfig()

        path = os.path.expanduser('~/.ssh/config')
        if os.path.exists(path):
            with open(path) as open_file:
                ssh_config.parse(open_file)

        # Create a fake hostname like "dev.myproject.ssha" to allow users to
        # set options in ~/.ssh/config based on the environment and project.
        hostname_parts = (get('config.name'), get('ssha.name'), 'ssha')
        hostname = '.'.join(filter(None, hostname_parts))

        result = ssh_config.lookup(hostname)

        if 'identityfile' not in result:
            result['identityfile'] = [
                '~/.ssh/id_rsa',
                '~/.ssh/id_dsa',
                '~/.ssh/id_ecdsa',
                '~/.ssh/id_ed25519',
            ]

        if 'user' not in result:
            user = os.environ.get('USER')
            if user:
                result['user'] = user

        _ssh_config.update(result)

    return _ssh_config.get(key, [])


def _is_used(data, key):
    """
    Checks if a key is used as a variable anywhere else in the config.

    """
    if isinstance(data, basestring):
        for var in re.findall('\$\{(.+?)\}', data):
            if var == key:
                return True
    elif isinstance(data, dict):
        for value in data.values():
            if _is_used(value, key):
                return True
    elif isinstance(data, list):
        for value in data:
            if _is_used(value, key):
                return True
    return False


def _merge(target, source):
    for key in source:
        if key in target:
            if isinstance(target[key], dict) and isinstance(source[key], dict):
                _merge(target[key], source[key])
            else:
                target[key] = source[key]
        else:
            target[key] = source[key]


def add(name, value):
    data = {}
    here = data
    for key in name.split('.'):
        last = here
        here[key] = {}
        here = here[key]
    last[key] = value
    update(data)


def get(key, default=None):

    value = _get(key, default)

    if not value:
        return value

    if isinstance(value, (dict, list)):
        value = copy.deepcopy(value)

    return render(value)


def load(name):
    """
    Loads a config from the settings.

    """

    update(settings.all())

    config_specific_settings = _config.pop('config', None) or {}
    if name:
        if name not in names():
            errors.string_exit('config {} not found in .ssha file'.format(name))
        for config_name in config_specific_settings:
            if fnmatch(name, config_name):
                update(config_specific_settings[config_name])
        add('config.name', name)

    iam_group_specific_settings = get('iam.group')
    if iam_group_specific_settings:
        from . import iam
        for group in iam.groups():
            if group in iam_group_specific_settings:
                update(iam_group_specific_settings[group])

    # Default to SSH's default user.
    if not _get('ssh.username'):
        user = _get_ssh_config('user')
        if user:
            add('ssh.username', user)
        elif is_used_as_variable('ssh.username'):
            errors.string_exit('Could not determine a username to use for ssh.username')

    if _get('bastion') and not _get('ssh.proxy_command'):
        from . import ssh
        if _get('ssh.user_known_hosts_file'):
            known_hosts_options = ['-o', 'UserKnownHostsFile=${ssh.user_known_hosts_file}']
        else:
            known_hosts_options = []
        proxy_command = ['ssh'] + known_hosts_options + ['-W', '%h:%p', '${bastion.address}']
        add('ssh.proxy_command', ssh.format_command(proxy_command))

    # To support configs like this:
    #   ssm.parameters.key = ["$(cat '${ssh.identityfile_public}')"]
    # If "ssh.identityfile_public" has been used as a variable, then find the
    # first identity file in the SSH config that has a matching ".pub" file.
    # The SSM document command would then add this public key to a user account
    # so that SSH key-based authentication will work.
    if is_used_as_variable('ssh.identityfile_public') and not _get('ssh.identityfile_public'):
        tried = {}
        for private_key_path in _get_ssh_config('identityfile'):
            private_key_path = os.path.expanduser(private_key_path)
            public_key_path = private_key_path + '.pub'
            if os.path.exists(private_key_path) and os.path.exists(public_key_path):
                add('ssh.identityfile_public', public_key_path)
                break
            tried[private_key_path] = public_key_path
        else:
            error_lines = []
            error_lines.append('Could not find a key to use for ssh.identityfile_public')
            error_lines.append('Tried the following key pairs:')
            for private_key_path, public_key_path in sorted(tried.items()):
                error_lines.append('  ' + private_key_path + ' + ' + public_key_path)
            errors.string_exit('\n'.join(error_lines))

    # To support configs like this:
    #   ssh.user_known_hosts_file = "${ssm.host_keys_file}"
    # If "ssm.host_keys_file" has been used as a variable, then create a temp
    # file and set "ssm.host_keys_file" as the temp file path. The SSM code
    # will populate the file with the output of the SSM command. The SSM
    # command must print the server's SSH host keys for this to work.
    if is_used_as_variable('ssm.host_keys_file') and not _get('ssm.host_keys_file'):
        _tempfiles['host_keys_file'] = tempfile.NamedTemporaryFile(suffix='-ssha-known-hosts')
        add('ssm.host_keys_file', _tempfiles['host_keys_file'].name)


def names():
    ssha_settings = settings.all().get('ssha') or {}
    return ssha_settings.get('configs') or []


def regions():
    region = get('aws.region_name')
    if region:
        return [region]
    return get('ssha.regions') or []


def render(data):
    if isinstance(data, basestring):
        for var in re.findall('\$\{(.+?)\}', data):
            value = get(var)
            if value is None:
                raise KeyError(var)
            data = data.replace('${' + var + '}', value)
        if data.startswith('$(') and data.endswith(')'):
            data = _exec(data[2:-1])
    elif isinstance(data, dict):
        for key, value in data.items():
            data[key] = render(value)
    elif isinstance(data, list):
        data = [render(item) for item in data]
    return data


def reset():
    _config.clear()
    _ssh_config.clear()
    _tempfiles.clear()


def update(data):
    _merge(_config, data)


def is_used_as_variable(key):
    return _is_used(_config, key)
