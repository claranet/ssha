from __future__ import print_function
from __future__ import unicode_literals

from functools import wraps

import boto3
import boto3_session_cache
import botocore.session
from botocore.exceptions import ClientError, ParamValidationError

from . import config


_sessions = {}


def retry(attempts=3):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            tries = attempts
            while True:
                tries -= 1
                try:
                    return func(*args, **kwargs)
                except (ClientError, ParamValidationError) as error:
                    if tries > 0:
                        print('[ssha] {}'.format(error))
                    else:
                        raise
        return wrapped
    return wrapper


@retry()
def client(*args, **kwargs):
    return session().client(*args, **kwargs)


@retry()
def credentials(*args, **kwargs):
    return session().get_credentials(*args, **kwargs)


@retry()
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
