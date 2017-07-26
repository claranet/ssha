from __future__ import print_function

import argparse
import sys

from . import __version__, config, ec2, menu, settings, ssm, ssh


try:

    parser = argparse.ArgumentParser(prog=__package__)
    parser.add_argument('config', nargs='?', help='Configuration name')
    parser.add_argument('search', nargs='?', help='Instance search string')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
    parser.add_argument('--version', action='store_true', help='show the installed version and exit')

    args = parser.parse_args()

    if args.version:
        print(__version__)
        sys.exit(0)

    settings.load(verbose=args.verbose)

    configs = config.names()
    config_name = menu.choose_config(configs, args.config)
    config.load(config_name)

    instances = ec2.discover_instances()
    instance = menu.choose_instance(instances, args.search)
    if instance:

        bastion = ec2.discover_bastion(instance)

        if config.get('ssm'):
            ssm.send_command(instance, bastion)

        ssh.connect(instance, bastion)

    else:
        print('[ssha] no matching instances found')

except KeyboardInterrupt:
    pass
