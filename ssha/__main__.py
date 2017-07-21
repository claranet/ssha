from __future__ import print_function

import argparse

from . import config, ec2, menu, ssm, ssh


parser = argparse.ArgumentParser(prog=__package__)
parser.add_argument('config', help='Configuration file')
parser.add_argument('search', nargs='?', help='Search string')
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')

args = parser.parse_args()

config.load(args.config, verbose=args.verbose)

try:
    instances = ec2.find_instances()
    if instances:
        instance = menu.choose_instance(instances, args.search)
        if instance:
            bastion = ec2.find_bastion(instance, instances)
            if config.get('ssm'):
                ssm.add_ssh_key(instance, bastion)
            ssh.connect(instance, bastion)
    else:
        print('No matching instances found')
except KeyboardInterrupt:
    pass
