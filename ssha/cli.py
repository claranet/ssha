from __future__ import print_function

import argparse

from . import __version__, config, ec2, menu, settings, ssm, ssh


def main():
    try:

        parser = argparse.ArgumentParser(prog=__package__)
        parser.add_argument('config', nargs='?', help='Configuration name')
        parser.add_argument('search', nargs='?', help='Instance search string')
        parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
        parser.add_argument('--command', help='Command to run instead of ssh')
        parser.add_argument('--region', help='Region name')
        parser.add_argument('--settings', help='Path to the .ssha file')
        parser.add_argument('--version', action='store_true', help='show the installed version and exit')

        args = parser.parse_args()

        if args.version:
            print(__version__)
            return 0

        settings.load(settings_path=args.settings, verbose=args.verbose)

        configs = config.names()
        config_name = menu.choose_config(configs, args.config)
        config.load(config_name)

        regions = config.regions()
        region_name = menu.choose_config(regions, args.region)
        if region_name:
            config.add('aws.region_name', region_name)

        instances = ec2.discover_instances()
        instance = menu.choose_instance(instances, args.search, show_menu=not args.command)
        if instance:

            if not args.command and ssm.session_manager_enabled(instance):

                return ssm.start_session(instance)

            else:

                if config.get('bastion') and not config.get('bastion.disabled'):
                    bastion = ec2.discover_bastion(instance)
                else:
                    bastion = None

                if config.get('ssm'):
                    ssm.send_command(instance, bastion)

                return ssh.connect(instance, bastion, args.command)

        else:
            print('[ssha] no matching instances found')

    except KeyboardInterrupt:
        pass

    return 0
