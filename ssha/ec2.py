from __future__ import print_function

from . import aws, config, errors, ssm


_instances = []


def _describe_instances():

    ec2 = aws.client('ec2')

    print('[ssha] discovering ec2 instances')

    next_token = None
    while True:

        kwargs = {}
        if next_token:
            kwargs['NextToken'] = next_token

        response = ec2.describe_instances()
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            errors.json_exit(response)

        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                yield instance

        next_token = response.get('NextToken')
        if not next_token:
            break


def _filter_instances(instances, rules):
    result = []
    for instance in instances:
        if _rules_pass(instance, rules):
            result.append(instance)
    return result


def _instance_sort_key(instance):
    result = []
    for field in config.get('display.sort') or ['InstanceId']:
        value = instance
        for key in field.split('.'):
            value = value.get(key)
            if not value:
                break
        result.append(value or '')
    return result


def _rules_pass(obj, rules):

    for key, expected_value in rules.items():

        if key not in obj:
            return False

        if isinstance(expected_value, dict):
            nested_rules = expected_value
            if not _rules_pass(obj[key], nested_rules):
                return False

        elif obj[key] != expected_value:
            return False

    return True


def _find_instances(ec2_filters, ssm_filters):

    if not _instances:
        for instance in _describe_instances():
            tags = {}
            for tag in instance.get('Tags') or []:
                tags[tag['Key']] = tag['Value']
            instance['Tags'] = tags
            _instances.append(instance)

    instances = _instances

    if instances and ec2_filters:
        instances = _filter_instances(instances, ec2_filters)

    if instances and ssm_filters:
        for info in ssm.find_instances():
            for instance in instances:
                if instance['InstanceId'] == info['InstanceId']:
                    instance.update(info)
                    break
        instances = _filter_instances(instances, ssm_filters)

    return instances


def discover_bastion(instance):
    bastions = _find_instances(
        ec2_filters=config.get('bastion.ec2'),
        ssm_filters=config.get('bastion.ssm'),
    )
    for bastion in bastions:
        if bastion['InstanceId'] == instance['InstanceId']:
            return None
    if bastions:
        return bastions[0]
    else:
        errors.string_exit('Bastion not found')


def discover_instances():
    instances = _find_instances(
        ec2_filters=config.get('discover.ec2'),
        ssm_filters=config.get('discover.ssm'),
    )
    return sorted(instances, key=_instance_sort_key)


def label(instance):
    result = []
    for field in config.get('display.fields') or []:
        value = instance
        for key in field.split('.'):
            value = value.get(key)
        if value:
            result.append(value)
    return ' '.join(result) or instance['InstanceId']
