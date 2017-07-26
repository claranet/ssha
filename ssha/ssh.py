from __future__ import print_function

import os

from . import config


def _format_command(command):
    args = []
    for arg in command:
        if ' ' in arg:
            args.append('"' + arg + '"')
        else:
            args.append(arg)
    return ' '.join(args)


def _get_address(instance):

    username = config.get('ssh.username')

    # Don't add the username to the address when it is the current user,
    # because it would make no difference.
    if username == os.environ.get('USER'):
        username = None

    hostname = _get_hostname(instance)

    if username:
        return username + '@' + hostname
    else:
        return hostname


def _get_hostname(instance):
    return instance.get('PublicIpAddress') or instance['PrivateIpAddress']


def connect(instance, bastion):

    command = ['ssh']

    if config.get('verbose'):
        command += ['-v']

    identity_file = config.get('ssh.identity_file')
    if identity_file:
        # Don't add to the command when using the default identity,
        # because it would make no difference.
        if identity_file not in ('~/.ssh/id_dsa.pub', '~/.ssh/id_rsa.pub'):
            command += ['-i', identity_file]

    if bastion:
        config.add('bastion.address', _get_address(bastion))
        proxy_command = config.get('ssh.proxy_command')
        command += ['-o', 'ProxyCommand={}'.format(proxy_command)]

    command += [_get_address(instance)]

    print('[ssha] running {}'.format(_format_command(command)))

    os.execlp('ssh', *command)
