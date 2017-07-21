import boto3
import boto3_session_cache
import botocore.session

from . import config


def session():
    aws_config = config.get('aws') or {}
    profile = aws_config.pop('profile_name', None)
    botocore_session = botocore.session.Session(profile=profile)
    resolver = botocore_session.get_component('credential_provider')
    provider = resolver.get_provider('assume-role')
    provider.cache = boto3_session_cache.JSONFileCache()
    return boto3.Session(botocore_session=botocore_session, **aws_config)


def ec2():
    return session().client('ec2')


def ssm():
    return session().client('ssm')
