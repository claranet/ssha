import unittest

from ssha import config, settings


class TestConfig(unittest.TestCase):

    def setUp(self):
        # Reset the global settings and config objects before each test.
        settings.reset()
        config.reset()

    def test_add(self):
        # Add a simple top-level value.
        config.add('one', 'two')
        self.assertEqual(config.get('one'), 'two')

        # Add a nested value.
        config.add('three', {})
        config.add('three.four', 'five')
        self.assertEqual(config.get('three.four'), 'five')
        self.assertDictEqual(config.get('three'), {'four': 'five'})

    def test_config_names(self):
        # Add settings with regular and wildcard config names.
        settings.update({
            'ssha': {
                'configs': ['test-nonprod', 'test-prod'],
            },
            'config': {
                'test-nonprod': {
                    'value1': 'a',
                },
                '*-nonprod': {
                    'value2': 'b',
                },
                '*-prod': {
                    'value3': 'c',
                },
            },
        })

        # The test-nonprod config should match 2 configs.
        config.load('test-nonprod')
        self.assertEqual(config.get('value1'), 'a')
        self.assertEqual(config.get('value2'), 'b')
        self.assertEqual(config.get('value3'), None)

        # The test-prod config should match 1 config.
        config.reset()
        config.load('test-prod')
        self.assertEqual(config.get('value1'), None)
        self.assertEqual(config.get('value2'), None)
        self.assertEqual(config.get('value3'), 'c')
