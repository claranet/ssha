from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import time

from botocore.exceptions import ClientError

from . import aws, config, errors, ssh


def _send_command(instance_ids):

    document_name = config.get('ssm.document.name')
    parameters = config.get('ssm.parameters')

    print('[ssha] ssm send {document} to {instances}'.format(
        document=document_name,
        instances=' and '.join(instance_ids),
    ))

    ssm = aws.client('ssm')

    result = ssm.send_command(
        InstanceIds=instance_ids,
        DocumentName=document_name,
        Parameters=parameters,
    )

    try:
        command_id = result['Command']['CommandId']
    except Exception:
        errors.json_exit(result)

    return command_id


def _wait_for_command(instance_ids, command_id):

    ssm = aws.client('ssm')

    outputs = {}

    for instance_id in instance_ids:

        result = {'Status': 'Pending'}

        while result['Status'] in ('Pending', 'InProgress', 'Delayed'):
            time.sleep(0.25)
            try:
                result = ssm.get_command_invocation(
                    CommandId=command_id,
                    InstanceId=instance_id,
                )
            except ClientError:
                pass

        if result['Status'] != 'Success':
            errors.json_exit(result)

        print('[ssha] ssm command finished on {}'.format(instance_id))
        outputs[instance_id] = result['StandardOutputContent']

    return outputs


def find_instances():

    ssm = aws.client('ssm')
    paginator = ssm.get_paginator('describe_instance_information')
    page_iterator = paginator.paginate()

    instance_info_list = []
    for page in page_iterator:
        if page['ResponseMetadata']['HTTPStatusCode'] != 200:
            errors.json_exit(page)

        instance_info_list += page['InstanceInformationList']

    return instance_info_list


def send_command(instance, bastion):

    instance_ids = [inst['InstanceId'] for inst in (instance, bastion) if inst]

    command_id = _send_command(
        instance_ids=instance_ids,
    )

    outputs = _wait_for_command(
        instance_ids=instance_ids,
        command_id=command_id,
    )

    host_keys_file = config.get('ssm.host_keys_file')
    if host_keys_file:
        instance_ips = {}

        if bastion:
            instance_id = bastion['InstanceId']
            instance_ips[instance_id] = ssh.get_ip(bastion, connect_through_bastion=False)

        instance_id = instance['InstanceId']
        instance_ips[instance_id] = ssh.get_ip(instance, connect_through_bastion=bool(bastion))

        with open(host_keys_file, 'w') as open_file:
            for instance_id, ip in instance_ips.items():
                host_keys = outputs[instance_id]
                for line in host_keys.splitlines():
                    # Replace hostname from the host keys line
                    # with the instance's hostname.
                    line = re.sub(r'^[^#\s]+', ip, line)
                    open_file.write(line + '\n')


def session_manager_enabled(instance):

    # Check if enabled in config.
    if not config.get('ssm.session_manager', False):
        return False

    # Check if agent is installed.
    if not instance.get('AgentVersion'):
        return False

    # Check if required plugin is installed.
    if os.system('which session-manager-plugin > /dev/null') != 0:
        return False

    return True


def start_session(instance):

    session = aws.session()
    creds = session.get_credentials().get_frozen_credentials()

    os.putenv('AWS_DEFAULT_REGION', session.region_name)
    os.putenv('AWS_ACCESS_KEY_ID', creds.access_key)
    os.putenv('AWS_SECRET_ACCESS_KEY', creds.secret_key)
    os.putenv('AWS_SESSION_TOKEN', creds.token)

    command = 'aws ssm start-session --target {}'.format(instance['InstanceId'])
    print('[ssha] running {}'.format(command))
    return os.system(command)
