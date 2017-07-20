import boto3

from . import config

_sessions = []
_clients = {}


def _session():
    if not _sessions:
        aws = config.get('aws') or {}
        _sessions.append(boto3.Session(**aws))
    return _sessions[0]


def ec2():
    if 'ec2' not in _clients:
        _clients['ec2'] = _session().client('ec2')
    return _clients['ec2']


def ssm():
    if 'ssm' not in _clients:
        _clients['ssm'] = _session().client('ssm')
    return _clients['ssm']
