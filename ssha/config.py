import copy
import re
import subprocess

from . import errors, settings


_config = {}


def _exec(command):
    return subprocess.check_output(command, shell=True).strip()


def _exec_all(data):
    if isinstance(data, basestring):
        for var in re.findall('\$\{(.+?)\}', data):
            data = data.replace('${' + var + '}', get(var))
        if data.startswith('$(') and data.endswith(')'):
            data = _exec(data[2:-1])
    elif isinstance(data, dict):
        for key, value in data.items():
            data[key] = _exec_all(value)
    elif isinstance(data, list):
        data = [_exec_all(item) for item in data]
    return data


def _get(key, default=None):
    value = _config
    for key in key.split('.'):
        value = value.get(key)
        if not value:
            break
    return value or default


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
    last_key = name
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

    return _exec_all(value)


def load(name):
    """
    Loads a config from the settings.

    """

    update(settings.all())

    config_specific_settings = _config.pop('config', None) or {}
    if name:
        if name not in names():
            errors.string_exit('config {} not found in .ssha file'.format(name))
        if name in config_specific_settings:
            update(config_specific_settings[name])
        add('config.name', name)

    if not _get('ssh.username'):
        add('ssh.username', '$(whoami)')

    if _get('bastion') and not _get('ssh.proxy_command'):
        add('ssh.proxy_command', 'ssh -W %h:%p ${bastion.address}')

    iam_group_specific_settings = get('iam.group')
    if iam_group_specific_settings:
        from . import iam
        for group in iam.groups():
            if group in iam_group_specific_settings:
                update(iam_group_specific_settings[group])


def names():
    ssha_settings = settings.all().get('ssha') or {}
    return ssha_settings.get('configs') or []


def update(data):
    _merge(_config, data)
