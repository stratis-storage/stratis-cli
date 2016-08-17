"""
Test operation of StratisdConstants class and related classes.
"""


import unittest

from cli._stratisd_constants import StratisdConstants

class BuildTestCase(unittest.TestCase):
    """
    Test building the class.
    """

    def testBuild(self):
        """
        Test that building yields a class w/ the correct properties.
        """
        fields = {'FIELD1' : 2, 'FIELD2': 0}
        klass = StratisdConstants.build_class('Test', fields)
        for key, item in fields.items():
            self.assertEqual(getattr(klass, key), item)
