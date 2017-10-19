#!/usr/bin/env python

from setuptools import setup

import ssha


setup(
    name='ssha',
    version=ssha.__version__,
    description='SSH into AWS EC2 instances',
    author='Raymond Butcher',
    author_email='ray.butcher@claranet.uk',
    url='https://github.com/claranet/ssha',
    license='MIT License',
    packages=(
        'ssha',
    ),
    scripts=(
        'bin/ssha',
    ),
    install_requires=(
        'botocore>=1.5.8',
        'boto3',
        'boto3-session-cache',
        'paramiko',
        'pyhcl',
    ),
)
