from __future__ import print_function

import os

from . import config


def _get_hostname(instance):
    return instance.get('PublicIpAddress') or instance['PrivateIpAddress']


def connect(instance, bastion):

    command = ['ssh']

    if config.get('verbose'):
        command += ['-v']

    if bastion:
        command += ['-A', '-t', _get_hostname(bastion), 'ssh']

    command += [_get_hostname(instance)]

    if config.get('verbose'):
        print('Running {}'.format(' '.join(command)))

    os.execlp('ssh', *command)
