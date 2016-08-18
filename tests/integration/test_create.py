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
    Test 'create' parsing.
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

    @unittest.skip("not really handling this")
    def testCreate(self):
        """
        Create expects success unless devices are already occupied.
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
        Create should always succeed with force.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--force', '1'] + \
               [self._POOLNAME] + \
               [d.device_node for d in _device_list(_DEVICES, 1)]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should always succeed when force is set.")


class Create3TestCase(unittest.TestCase):
    """
    Test 'create' on name collision.
    """
    _MENU = ['create']
    _POOLNAME = 'deadpool'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = \
           ['python', _CLI, 'create'] + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        subprocess.check_call(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testCreate(self):
        """
        Create should fail trying to create new pool with same name as previous.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               [self._POOLNAME] + \
               [d.device_node for d in _device_list(_DEVICES, 1)]
            subprocess.check_call(command_line)
            self.fail("Should fail on name collision.")
        except subprocess.CalledProcessError:
            pass

    def testForce(self):
        """
        Create should fail trying to create new pool with same name as previous,
        regardless of --force parameter.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--force', '1'] + \
               [self._POOLNAME] + \
               [d.device_node for d in _device_list(_DEVICES, 1)]
            subprocess.check_call(command_line)
            self.fail("Should fail on name collision, regardless of force.")
        except subprocess.CalledProcessError:
            pass
