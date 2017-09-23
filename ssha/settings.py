from __future__ import print_function

import copy
import hcl
import os
import sys

from . import errors


_settings = {}


def _find_user_settings_path():
    """
    Returns the path to the user settings file for the operating system.

    This file is for user specific configuration
    (e.g. custom path to ssh public key).
    """

    if sys.platform == 'linux' or sys.platform == 'posix':
        return os.path.join(os.environ['HOME'], '.config/ssha/config')
    elif sys.platform == 'win32':
        return os.path.join(os.environ['LOCALAPPDATA'], 'ssha\config')
    else:
        print((
            "Unknown operating system: {} as a result ssha does not know "
            "where to find user config.").format(sys.platform))
        return None


def _find_settings_path():

    cwd = os.path.realpath(os.getcwd())

    while cwd and cwd != '/':
        path = os.path.join(cwd, '.ssha')
        if os.path.isfile(path):
            return path
        cwd = os.path.dirname(cwd)

    return None


def _load(path):
    try:
        if os.path.exists(path) and os.path.isfile(path):
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
        print('[ssha] finding settings files')
    _settings.update(defaults)

    settings_files_paths = []
    settings_files_paths.append(_find_settings_path())
    settings_files_paths.append(_find_user_settings_path())

    if not settings_files_paths[0]:
        errors.string_exit((
            'Could not find .ssha file in current directory or parent '
            'directories'))

    for path in settings_files_paths:
        if path:
            if defaults.get('verbose'):
                print('[ssha] loading {}'.format(path))
            data = _load(path)
            if data:
                _settings.update(data)
