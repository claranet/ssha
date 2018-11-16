from __future__ import print_function
from __future__ import unicode_literals

import errno
import os
import sys

from . import config


def _get_address(instance_ip):

    username = config.get('ssh.username')

    # Don't add the username to the address when it is the current user,
    # because it would make no difference.
    if username == os.environ.get('USER'):
        username = None

    if username:
        return username + '@' + instance_ip
    else:
        return instance_ip


def connect(instance, bastion, command):

    bastion_hostname = config.get('bastion.hostname')
    if not bastion_hostname and bastion:
        bastion_hostname = get_ip(bastion, connect_through_bastion=False)
    if bastion_hostname:
        config.add('bastion.address', _get_address(bastion_hostname))

    instance_ip = get_ip(instance, connect_through_bastion=bool(bastion_hostname))
    config.add('hostname', instance_ip)

    instance_address = _get_address(instance_ip)
    config.add('address', instance_address)

    ssh_command = ['ssh']
    if config.get('verbose'):
        ssh_command += ['-v']
    user_known_hosts_file = config.get('ssh.user_known_hosts_file')
    if user_known_hosts_file:
        ssh_command += ['-o', 'UserKnownHostsFile={}'.format(user_known_hosts_file)]
    if bastion_hostname:
        proxy_command = config.get('ssh.proxy_command')
        ssh_command += ['-o', 'ProxyCommand={}'.format(proxy_command)]
    ssh_command += [instance_address]
    config.add('ssh.cmd', format_command(ssh_command))

    if command:

        command = config.render(command)
        print('[ssha] running {}'.format(command))
        return os.system(command)

    else:

        print('[ssha] running {}'.format(config.get('ssh.cmd')))
        run(ssh_command)


def format_command(command):
    args = []
    for arg in command:
        if ' ' in arg:
            args.append('"' + arg + '"')
        else:
            args.append(arg)
    return ' '.join(args)


def get_ip(instance, connect_through_bastion):
    if connect_through_bastion:
        return instance['PrivateIpAddress']
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
