"""
Test 'create'.
"""

import subprocess
import unittest

from ._constants import _CLI
from ._constants import _DEVICES

from ._misc import _device_list
from ._misc import Service


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
               ['--force', '2'] + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should not fail because pool is not there.")


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
        The pool was just created, so must be destroyable w/out force.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should always succeed, pool has no volumes.")

    def testWithForce(self):
        """
        Since it should succeed w/out force, it should succeed w/ force.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--force', '1'] + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should always succeed with any force value.")


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

    @unittest.expectedFailure
    def testWithoutForce(self):
        """
        This should fail with a force value of 0, since it has a volume.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
            self.fail("No force value, and pool has an allocated volume.")
        except subprocess.CalledProcessError:
            pass

    def testWithForce1(self):
        """
        Should succeed w/ force value of 1, since it has volumes but no data.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--force', '1'] + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should succeed with force value of 1.")

    def testWithForce2(self):
        """
        Should succeed w/ force value of 2, since it has volumes but no data.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--force', '2'] + \
               [self._POOLNAME]
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("Should succeed with force value of 1.")
