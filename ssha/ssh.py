from __future__ import print_function

import errno
import os

from . import config


def _get_address(instance):

    username = config.get('ssh.username')

    # Don't add the username to the address when it is the current user,
    # because it would make no difference.
    if username == os.environ.get('USER'):
        username = None

    hostname = get_hostname(instance)

    if username:
        return username + '@' + hostname
    else:
        return hostname


def connect(instance, bastion):

    command = ['ssh']

    if config.get('verbose'):
        command += ['-v']

    user_known_hosts_file = config.get('ssh.user_known_hosts_file')
    if user_known_hosts_file:
        command += ['-o', 'UserKnownHostsFile={}'.format(user_known_hosts_file)]

    if bastion:
        config.add('bastion.address', _get_address(bastion))
        proxy_command = config.get('ssh.proxy_command')
        command += ['-o', 'ProxyCommand={}'.format(proxy_command)]

    command += [_get_address(instance)]

    print('[ssha] running {}'.format(format_command(command)))
    run(command)


def format_command(command):
    args = []
    for arg in command:
        if ' ' in arg:
            args.append('"' + arg + '"')
        else:
            args.append(arg)
    return ' '.join(args)


def get_hostname(instance):
    return instance.get('PublicIpAddress') or instance['PrivateIpAddress']


def run(command):
    child_pid = os.fork()
    if child_pid == 0:
        os.execlp(command[0], *command)
    else:
        while True:
            try:
                os.waitpid(child_pid, 0)
            except OSError as error:
                if error.errno == errno.ECHILD:
                    # No child processes.
                    # It has exited already.
                    break
                elif error.errno == errno.EINTR:
                    # Interrupted system call.
                    # This happens when resizing the terminal.
                    pass
                else:
                    # An actual error occurred.
                    raise
