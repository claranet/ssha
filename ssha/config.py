import copy
import re
import subprocess

from . import errors, settings


_config = {}


def _exec(command):
    return subprocess.check_output(command, shell=True).strip()


def _exec_all(data):
    if isinstance(data, basestring):
        for var in re.findall('\$\{(.+?)\}', data):
            data = data.replace('${' + var + '}', get(var))
        if data.startswith('$(') and data.endswith(')'):
            data = _exec(data[2:-1])
    elif isinstance(data, dict):
        for key, value in data.items():
            data[key] = _exec_all(value)
    elif isinstance(data, list):
        data = [_exec_all(item) for item in data]
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


def load(name):
    """
    Loads a config from the settings.

    """

    _config.update(settings.all())
    config_specific_settings = _config.pop('config', None) or {}

    if name:
        if name not in names():
            errors.string_exit('Config {} is not defined in the .ssha file'.format(name))
        if name in config_specific_settings:
            _merge(_config, config_specific_settings[name])
        _merge(_config, {'config': {'name': name}})


def names():
    ssha_settings = settings.all().get('ssha') or {}
    return ssha_settings.get('configs') or []
