import subprocess
import sys
import toml


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


def get(key):
    keys = key.split('.')
    value = _config
    for key in keys:
        value = value.get(key)
        if value is None:
            return None

    return _exec_all(value)


def load(path, **defaults):
    _config.update(defaults)
    try:
        with open(path) as config_file:
            data = toml.load(config_file)
    except IOError as error:
        sys.stderr.write('Error reading config: {}\n'.format(error))
        sys.exit(1)
    except Exception as error:
        sys.stderr.write('Error parsing config: {}\n'.format(error))
        sys.exit(1)
    else:
        _config.update(data)
