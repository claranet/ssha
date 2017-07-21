import copy
import os
import subprocess
import sys
import toml

from . import errors


_config = {}


def _exec(command):
    return subprocess.check_output(command, shell=True).strip()


def _exec_all(data):
    if isinstance(data, basestring):
        if data.startswith('$(') and data.endswith(')'):
            data = _exec(data[2:-1])
    elif isinstance(data, dict):
        for key, value in data.items():
            data[key] = _exec_all(value)
    elif isinstance(data, list):
        data = [_exec_all(item) for item in data]
    return data


def _find_dot_files(path=None):

    if path:
        if os.path.isfile(path):
            path = os.path.dirname(path)
    else:
        path = os.getcwd()
    path = os.path.realpath(path)

    paths = []
    while path and path != '/':
        dot_path = os.path.join(path, '.ssha')
        if os.path.isfile(dot_path):
            paths.append(dot_path)
        path = os.path.dirname(path)
    return paths


def _load(path):
    try:
        with open(path) as config_file:
            data = toml.load(config_file)
    except IOError as error:
        errors.string_exit('Error reading config: {}'.format(error))
    except Exception as error:
        errors.string_exit('Error parsing config: {}'.format(error))

    # Make [configs] paths relative to the config file.
    for key in data.get('configs') or []:
        data['configs'][key] = os.path.join(
            os.path.dirname(path),
            data['configs'][key],
        )

    return data


def _merge(target, source):
    for key in source:
        if key in target:
            if isinstance(target[key], dict) and isinstance(source[key], dict):
                _merge(target[key], source[key])
            else:
                target[key] = source[key]
        else:
            target[key] = source[key]


def get(key):

    keys = key.split('.')
    value = _config
    for key in keys:
        value = value.get(key)
        if value is None:
            return None

    if isinstance(value, (dict, list)):
        value = copy.deepcopy(value)

    return _exec_all(value)


def load(path, **defaults):
    _config.update(defaults)

    # Load all of the .ssha config files first to get the [configs] mappings.
    dot_configs = {}
    for dot_path in _find_dot_files():
        _merge(dot_configs, _load(dot_path))
    _merge(_config, dot_configs)

    # If there is a mapping for this path then use it.
    configs = get('configs') or {}
    path = configs.get(path) or path

    # Now load the specified config file.
    _merge(_config, _load(path))

    # Now load the .ssha configs again so any of their values take priority.
    _merge(_config, dot_configs)
