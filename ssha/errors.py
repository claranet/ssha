import json
import sys


def json_exit(data):
    sys.stderr.write('ERROR:\n')
    if data:
        try:
            json.dump(data, sys.stderr, indent=2)
        except Exception:
            sys.stderr.write(data)
    sys.exit(1)


def string_exit(message):
    sys.stderr.write('ERROR:\n')
    sys.stderr.write(message)
    sys.stderr.write('\n')
    sys.exit(1)
