from __future__ import print_function

import os

from . import config


def _get_address(instance):
    hostname = instance.get('PublicIpAddress') or instance['PrivateIpAddress']
    username = config.get('ssh.username')
    if username:
        return username + '@' + hostname
    else:
        return hostname


def connect(instance, bastion):

    command = ['ssh']

    if config.get('verbose'):
        command += ['-v']

    identity_file = config.get('ssh.identity_file')
    if identity_file:
        command += ['-i', identity_file]

    if bastion:
        command += ['-A', '-t', _get_address(bastion), 'ssh']

    command += [_get_address(instance)]

    print('[ssha] running {}'.format(' '.join(command)))

    os.execlp('ssh', *command)
