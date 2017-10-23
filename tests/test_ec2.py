import unittest

from ssha import ec2


class TestEC2(unittest.TestCase):

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
