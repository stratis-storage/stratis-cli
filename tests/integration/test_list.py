"""
Test 'create'.
"""

import unittest

from cli._main import run

from ._constants import _DEVICES

from ._misc import _device_list
from ._misc import Service


class ListTestCase(unittest.TestCase):
    """
    Test 'list'.
    """
    _MENU = ['list']

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

    def testList(self):
        """
        List should just succeed.
        """
        command_line = self._MENU
        all(run(command_line))


class List2TestCase(unittest.TestCase):
    """
    Test 'list' with something actually to list.
    """
    _MENU = ['list']
    _POOLNAME = 'deadpool'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = \
           ['create'] + [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testList(self):
        """
        List should just succeed.
        """
        command_line = self._MENU
        all(run(command_line))
