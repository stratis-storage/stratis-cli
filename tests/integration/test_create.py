"""
Test 'create'.
"""

import os
import subprocess
import unittest

from cli import run

from ._constants import _CLI
from ._constants import _DEVICES
from ._constants import _STRATISD
from ._constants import _STRATISD_EXECUTABLE

from ._misc import _device_list


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
            execution = subprocess.check_call(command_line)
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
            execution = subprocess.check_call(command_line)
            self.fail("Should have failed on --force set.")
        except subprocess.CalledProcessError as err:
            pass

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
            execution = subprocess.check_call(command_line)
            self.fail("Should have failed on --redundancy value.")
        except subprocess.CalledProcessError as err:
            pass
