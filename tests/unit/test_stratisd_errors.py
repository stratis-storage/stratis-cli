"""
Test constructing StratisdError class.
"""


import unittest

from cli._stratisd_errors import StratisdErrorsGen

class BuildTestCase(unittest.TestCase):
    """
    Test building the class.
    """

    def testBuild(self):
        """
        Test that building yields a class w/ the correct properties.
        """
        fields = {'FIELD1' : 2, 'FIELD2': 0}
        klass = StratisdErrorsGen.build_class(fields)
        for key, item in fields.items():
            self.assertEqual(getattr(klass, key), item)
