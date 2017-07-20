from . import aws, config, errors, ssm


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
            value = value[key]
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


def find_bastion(instance, instances):

    bastions = instances

    bastion_filters = config.get('bastion.filter')
    if not bastion_filters:
        return None

    for bastion_filter in bastion_filters.values():
        bastions = _filter_instances(bastions, bastion_filter)

    for bastion in bastions:
        if bastion['InstanceId'] == instance['InstanceId']:
            return None

    if bastions:
        return bastions[0]
    else:
        errors.string_exit('Bastion not found')


def find_instances():

    ec2 = aws.ec2()

    response = ec2.describe_instances()
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        errors.json_exit(response)

    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:

            tags = {}
            for tag in instance.get('Tags') or []:
                tags[tag['Key']] = tag['Value']
            instance['Tags'] = tags

            instances.append(instance)

    instances = _filter_instances(instances, config.get('filter.ec2'))

    if instances and config.get('filter.ssm'):

        for info in ssm.find_instances():
            for instance in instances:
                if instance['InstanceId'] == info['InstanceId']:
                    instance.update(info)
                    break

        instances = _filter_instances(instances, config.get('filter.ssm'))

    return sorted(instances, key=_instance_sort_key)
