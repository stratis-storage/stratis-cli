"""
Test 'create'.
"""

import subprocess
import unittest

from ._constants import _CLI
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
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("List should always succeed.")


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
           ['python', _CLI, 'create'] + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        subprocess.check_call(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testList(self):
        """
        List should just succeed.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("List should always succeed.")
