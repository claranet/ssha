from __future__ import print_function

import datetime
import operator

from . import aws, config, errors, ssm


_instances = []


def _describe_instances():

    ec2 = aws.client('ec2')

    print('[ssha] discovering ec2 instances')

    paginator = ec2.get_paginator('describe_instances')
    page_iterator = paginator.paginate(MaxResults=15)
    for page in page_iterator:
        if page['ResponseMetadata']['HTTPStatusCode'] != 200:
            errors.json_exit(page)
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                yield instance


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


def _rules_pass(obj, rules, compare=operator.eq):

    for key, expected_value in rules.items():

        if isinstance(expected_value, dict):

            if key.endswith('NotEqual'):
                nested_compare = operator.ne
                key = key[:-len('NotEqual')]
            else:
                nested_compare = compare

            nested_rules_passed = _rules_pass(
                obj=obj.get(key) or {},
                rules=expected_value,
                compare=nested_compare,
            )
            if not nested_rules_passed:
                return False

        elif not compare(obj.get(key), expected_value):
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
        if isinstance(value, datetime.datetime):
            value = '[{:%Y-%m-%d %H:%M}]'.format(value)
        result.append(value or '')
    return result or [instance['InstanceId']]
