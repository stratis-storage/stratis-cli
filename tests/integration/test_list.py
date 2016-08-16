"""
Test 'create'.
"""

import os
import subprocess
import unittest

from ._constants import _CLI
from ._constants import _STRATISD
from ._constants import _STRATISD_EXECUTABLE


class ListTestCase(unittest.TestCase):
    """
    Test 'list'.
    """
    _MENU = ['list']

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
