import unittest

from ssha import config


class TestConfig(unittest.TestCase):

    def setUp(self):
        # Reset the global config before each test.
        config._config = {}

    def test_add(self):
        # Add a simple top-level value.
        config.add('one', 'two')
        self.assertEqual(config.get('one'), 'two')

        # Add a nested value.
        config.add('three', {})
        config.add('three.four', 'five')
        self.assertEqual(config.get('three.four'), 'five')
        self.assertDictEqual(config.get('three'), {'four': 'five'})
