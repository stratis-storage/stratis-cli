"""
Test 'create'.
"""

import subprocess
import unittest

from .._constants import _CLI
from .._constants import _DEVICES

from .._misc import _device_list
from .._misc import Service


class CreateTestCase(unittest.TestCase):
    """
    Test creating a volume w/out a pool.
    """
    _MENU = ['logical', 'create']
    _POOLNAME = 'deadpool'
    _VOLNAMES = ['oubliette', 'mnemosyne']

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

    def testCreation(self):
        """
        Creation of the volume must fail since pool is not specified.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               [self._POOLNAME] + \
               self._VOLNAMES
            subprocess.check_call(command_line)
            self.fail("Should have failed, since there is no pool.")
        except subprocess.CalledProcessError:
            pass


@unittest.skip("Creation of a volume could fail if no room in pool.")
class Create2TestCase(unittest.TestCase):
    """
    Test creating a volume w/ a pool.
    """
    _MENU = ['logical', 'create']
    _POOLNAME = 'deadpool'
    _VOLNAMES = ['oubliette', 'mnemosyne']

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

    def testCreation(self):
        """
        Creation of the volume should succeed since pool is available.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               [self._POOLNAME] + \
               self._VOLNAMES
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should have failed, since there is no pool.")
