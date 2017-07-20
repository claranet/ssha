#!/usr/bin/env python

from setuptools import setup

setup(
    name='ssha',
    version='0.1.0',
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
        'boto3',
        'toml',
    ),
)
