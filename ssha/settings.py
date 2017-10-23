from __future__ import print_function
from __future__ import unicode_literals

import copy
import hcl
import operator
import os
import re

from distutils.version import StrictVersion

from . import errors, __version__


_settings = {}

operators = {
    None: operator.eq,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    ">": operator.gt,
}

pattern = re.compile(
    r'\s*'
    r'(?P<operator>[<=>!]{1,2})?\s*'
    r'(?P<version>.+)\s*'
)


def _find_settings_path(path):
    if path:
        if os.path.isfile(path):
            return path
        errors.string_exit('Could not find .ssha file: {}'.format(path))

    cwd = os.path.realpath(os.getcwd())

    while cwd and cwd != '/':
        path = os.path.join(cwd, '.ssha')
        if os.path.isfile(path):
            return path
        cwd = os.path.dirname(cwd)

    errors.string_exit('Could not find .ssha file in current directory or parent directories')


def _load(path):
    try:
        with open(path) as settings_file:
            return hcl.load(settings_file)
    except IOError as error:
        errors.string_exit('Error reading settings: {}'.format(error))
    except Exception as error:
        errors.string_exit('Error parsing settings: {}'.format(error))


def _validate_version(data):
    ssha_settings = data.get('ssha') or {}
    version = ssha_settings.get('version')
    if version is None:
        return

    ssha_version = StrictVersion(__version__)
    requirements = version.split(',')
    for requirement in requirements:
        matched = pattern.match(requirement)
        if matched is None:
            errors.string_exit('Error parsing ssha version: {}'.format(requirement))

        spec_operator = matched.group('operator')
        if spec_operator not in operators:
            errors.string_exit('Error parsing operator in ssha version: {}'.format(requirement))

        try:
            spec_version = StrictVersion(matched.group('version'))
        except ValueError as error:
            errors.string_exit('Error parsing ssha version: {}'.format(error))

        if not operators[spec_operator](ssha_version, spec_version):
            errors.string_exit("Current ssha version {} doesn't meet requirements in settings: {}".format(
                ssha_version, requirement
            ))


def all():
    return copy.deepcopy(_settings)


def load(**defaults):
    if defaults.get('verbose'):
        print('[ssha] finding settings file')
    update(defaults)

    settings_path = defaults.get('settings_path')
    path = _find_settings_path(settings_path)

    if defaults.get('verbose'):
        print('[ssha] loading {}'.format(path))
    data = _load(path)
    _validate_version(data)
    update(data)


def reset():
    _settings.clear()


def update(data):
    _settings.update(data)
