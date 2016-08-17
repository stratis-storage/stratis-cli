"""
Test 'create'.
"""

import subprocess
import unittest

from ._constants import _CLI
from ._constants import _DEVICES

from ._misc import _device_list
from ._misc import Service


@unittest.skip("waiting for DestroyPool to be fixed")
class Destroy1TestCase(unittest.TestCase):
    """
    Test 'destroy' on empty database.

    'destroy' should always succeed on an empty database.
    """
    _MENU = ['destroy']
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

    def testWithoutForce(self):
        """
        Destroy should succeed w/out --force.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should not fail because pool is not there.")

    def testWithForce(self):
        """
        If pool does not exist and --force is set, command should succeed.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--force'] + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should not fail because pool is not there.")


@unittest.skip("waiting for DestroyPool to be fixed")
class Destroy2TestCase(unittest.TestCase):
    """
    Test 'destroy' on database which contains the given pool.
    """
    _MENU = ['destroy']
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

    def testWithoutForce(self):
        """
        Whether or not destroy succeeds depends on the state of the pool.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should not fail because pool is not there.")

    def testWithForce(self):
        """
        Whether or not destroy succeeds depends on the state of the pool.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--force'] + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should not fail because pool is not there.")


@unittest.skip("waiting for DestroyPool to be fixed")
class Destroy3TestCase(unittest.TestCase):
    """
    Test 'destroy' on database which contains the given pool and a volume.

    Verify that the volume is gone when the pool is gone.
    """
    _MENU = ['destroy']
    _POOLNAME = 'deadpool'
    _VOLNAME = 'vol'

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

        command_line = \
           ['python', _CLI, 'logical', 'create'] + \
           [self._POOLNAME] + \
           [self._VOLNAME]
        subprocess.check_call(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testWithoutForce(self):
        """
        Whether or not destroy succeeds depends on the state of the pool.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should not fail because pool is not there.")

    def testWithForce(self):
        """
        Whether or not destroy succeeds depends on the state of the pool.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--force'] + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should not fail because pool is not there.")
