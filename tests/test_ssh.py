import unittest

from ssha.ssh import format_command


class TestSSH(unittest.TestCase):

    def test_format_command(self):
        cmd = ('ssh', '-o', 'hello hello', 'localhost')
        result = format_command(cmd)
        self.assertEqual(result, 'ssh -o "hello hello" localhost')
