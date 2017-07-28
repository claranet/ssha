from __future__ import print_function

import boto3
import boto3_session_cache
import botocore.session

from . import config


_sessions = {}


def client(*args, **kwargs):
    return session().client(*args, **kwargs)


def resource(*args, **kwargs):
    return session().resource(*args, **kwargs)


def session():
    aws_config = config.get('aws') or {}
    profile = aws_config.pop('profile_name', None)
    if 'botocore' not in _sessions:
        print('[ssha] creating aws session')
        _sessions['botocore'] = botocore.session.Session(profile=profile)
        resolver = _sessions['botocore'].get_component('credential_provider')
        provider = resolver.get_provider('assume-role')
        provider.cache = boto3_session_cache.JSONFileCache()
    return boto3.Session(botocore_session=_sessions['botocore'], **aws_config)
