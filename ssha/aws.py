from __future__ import print_function
from __future__ import unicode_literals

import boto_source_profile_mfa

from botocore.exceptions import ClientError, ParamValidationError

from functools import wraps

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
    return boto_source_profile_mfa.get_session(**aws_config)
