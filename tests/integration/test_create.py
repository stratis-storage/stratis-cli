"""
Test 'create'.
"""

import os
import random
import subprocess
import unittest

import pyudev

from cli import run

_STRATISD = '/home/mulhern/my-contributions/stratisd'
_STRATISD_EXECUTABLE = 'stratisd'
_CLI = '/home/mulhern/my-projects/cli/src/main.py'

_DEVICES = list(pyudev.Context().list_devices(subsystem='block'))

def _device_list(devices, minimum):
    """
    Get a randomly selected list of devices with at least ``minimum`` elements.

    :param devices: list of device objects
    :type devices: list of pyudev.Device
    :param int minimum: the minimum number of devices, must be at least 0
    """
    limit = random.choice(range(minimum, len(devices)))
    indices = random.sample(range(len(devices)), limit)
    return [devices[i] for i in indices]


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
