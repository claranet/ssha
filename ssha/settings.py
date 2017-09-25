from __future__ import print_function

import copy
import hcl
import os

from . import errors


_settings = {}


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


def all():
    return copy.deepcopy(_settings)


def load(**defaults):
    if defaults.get('verbose'):
        print('[ssha] finding settings file')
    _settings.update(defaults)

    settings_path = defaults.get('settings_path')
    path = _find_settings_path(settings_path)

    if defaults.get('verbose'):
        print('[ssha] loading {}'.format(path))
    data = _load(path)
    _settings.update(data)
