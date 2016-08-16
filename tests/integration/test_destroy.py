"""
Test 'create'.
"""

import os
import subprocess
import unittest

from ._constants import _CLI
from ._constants import _DEVICES
from ._constants import _STRATISD
from ._constants import _STRATISD_EXECUTABLE

from ._misc import _device_list


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
        env = dict(os.environ)
        env['LD_LIBRARY_PATH'] = os.path.join(_STRATISD, 'lib')

        bin_path = os.path.join(_STRATISD, 'bin')

        self._stratisd = subprocess.Popen(
           os.path.join(bin_path, _STRATISD_EXECUTABLE),
           env=env
        )

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._stratisd.terminate()

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
        env = dict(os.environ)
        env['LD_LIBRARY_PATH'] = os.path.join(_STRATISD, 'lib')

        bin_path = os.path.join(_STRATISD, 'bin')

        self._stratisd = subprocess.Popen(
           os.path.join(bin_path, _STRATISD_EXECUTABLE),
           env=env
        )
        command_line = \
           ['python', _CLI, 'create'] + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        subprocess.check_call(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._stratisd.terminate()

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
