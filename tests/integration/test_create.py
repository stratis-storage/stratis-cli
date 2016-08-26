"""
Test 'create'.
"""

import unittest

from stratis_cli._main import run
from stratis_cli._errors import StratisCliRuntimeError

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
        command_line = \
           self._MENU + \
           ['--redundancy', 'raid6'] + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        with self.assertRaises(SystemExit):
            all(run(command_line))


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
        command_line = \
           self._MENU + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))

    def testForce(self):
        """
        Create should always succeed with force.
        """
        command_line = \
           self._MENU + \
           ['--force', '1'] + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))


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
           ['create', self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testCreate(self):
        """
        Create should fail trying to create new pool with same name as previous.
        """
        command_line = \
           self._MENU + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        with self.assertRaises(StratisCliRuntimeError):
            all(run(command_line))

    def testForce(self):
        """
        Create should fail trying to create new pool with same name as previous,
        regardless of --force parameter.
        """
        command_line = \
           self._MENU + \
           ['--force', '1'] + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        with self.assertRaises(StratisCliRuntimeError):
            all(run(command_line))
