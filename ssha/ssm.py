from __future__ import print_function

import time

from botocore.exceptions import ClientError

from . import aws, config, errors


def _send_run_command(instance_ids):

    if config.get('verbose'):
        print('Sending SSM command')

    ssm = aws.ssm()

    result = ssm.send_command(
        InstanceIds=instance_ids,
        DocumentName=config.get('ssm.document_name'),
        Parameters=config.get('ssm.parameters'),
    )

    try:
        command_id = result['Command']['CommandId']
    except Exception:
        errors.json_exit(result)

    return command_id


def _wait_for_command(instance_ids, command_id):

    ssm = aws.ssm()

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


def add_ssh_key(instance, bastion):

    instance_ids = [instance['InstanceId']]
    if bastion:
        instance_ids.append(bastion['InstanceId'])

    command_id = _send_run_command(
        instance_ids=instance_ids,
    )

    _wait_for_command(
        instance_ids=instance_ids,
        command_id=command_id,
    )


def find_instances():

    ssm = aws.ssm()

    response = ssm.describe_instance_information()
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        errors.json_exit(response)

    return response['InstanceInformationList']
