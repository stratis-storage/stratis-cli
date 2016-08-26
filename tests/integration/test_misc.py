"""
Test miscellaneous methods.
"""
import time
import unittest

from stratis_cli._connection import get_object

from ._misc import Service


class GetObjectTestCase(unittest.TestCase):
    """
    Test get_object method.
    """

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testNonExisting(self):
        """
        A proxy object is returned from a non-existant path.
        """
        time.sleep(1) # wait until the service is available
        self.assertIsNotNone(get_object('/this/is/not/an/object/path'))

    def testInvalid(self):
        """
        An invalid path causes an exception to be raised.
        """
        with self.assertRaises(ValueError):
            get_object('abc')
