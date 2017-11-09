import unittest

from ssha import config, ec2, settings


class TestEC2(unittest.TestCase):

    def setUp(self):
        # Reset the global settings and config objects before each test.
        settings.reset()
        config.reset()

    def test_label(self):
        # Test that missing display fields result in blank strings.
        config.add(
            'display.fields',
            ['InstanceId', 'Tags.Environment', 'Tags.Name'],
        )
        label = ec2.label({
            'InstanceId': 'abc',
            'Tags': {
                'Name': 'xyz',
            },
        })
        self.assertEqual(label, ['abc', '', 'xyz'])

    def test_rules_pass(self):

        bastion_instance = {
            'State': {
                'Name': 'Running',
            },
            'Tags': {
                'Service': 'bastion',
            },
        }

        web_instance = {
            'State': {
                'Name': 'Running',
            },
            'Tags': {
                'Service': 'web',
            },
        }

        is_bastion = {
            'State': {
                'Name': 'Running',
            },
            'Tags': {
                'Service': 'bastion',
            }
        }

        is_not_bastion = {
            'State': {
                'Name': 'Running',
            },
            'TagsNotEqual': {
                'Service': 'bastion',
            }
        }

        self.assertTrue(ec2._rules_pass(bastion_instance, is_bastion))
        self.assertTrue(ec2._rules_pass(web_instance, is_not_bastion))
        self.assertFalse(ec2._rules_pass(web_instance, is_bastion))
        self.assertFalse(ec2._rules_pass(bastion_instance, is_not_bastion))
