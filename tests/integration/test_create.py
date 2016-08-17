"""
Test 'create'.
"""

import subprocess
import unittest

from ._constants import _CLI
from ._constants import _DEVICES

from ._misc import _device_list
from ._misc import Service


class CreateTestCase(unittest.TestCase):
    """
    Test 'create'.
    """
    _MENU = ['create']
    _POOLNAME = 'deadpool'

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

    def testRedundancy(self):
        """
        Parser error on all redundancy that is not 'none'.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--redundancy', 'raid6'] + \
               [self._POOLNAME] + \
               [d.device_node for d in _device_list(_DEVICES, 1)]
            subprocess.check_call(command_line)
            self.fail("Should have failed on --redundancy value.")
        except subprocess.CalledProcessError:
            pass


@unittest.skip("Waiting for CreatePool to take force parameter.")
class Create2TestCase(unittest.TestCase):
    """
    Test 'create'.
    """
    _MENU = ['create']
    _POOLNAME = 'deadpool'

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

    def testCreate(self):
        """
        Create expects success.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               [self._POOLNAME] + \
               [d.device_node for d in _device_list(_DEVICES, 1)]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError as err:
            self.fail("Return code: %s" % err.returncode)

    def testForce(self):
        """
        Do not know exactly what to do about force.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--force'] + \
               [self._POOLNAME] + \
               [d.device_node for d in _device_list(_DEVICES, 1)]
            subprocess.check_call(command_line)
            self.fail("Should have failed on --force set.")
        except subprocess.CalledProcessError:
            pass
