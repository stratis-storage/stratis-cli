"""
Test 'create'.
"""

import os
import subprocess
import unittest

from ._constants import _CLI
from ._constants import _STRATISD
from ._constants import _STRATISD_EXECUTABLE


class StratisTestCase(unittest.TestCase):
    """
    Test meta information about stratisd.
    """
    _MENU = ['stratis']

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

    def testStratisVersion(self):
        """
        Getting version should just succeed.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--stratisd-version']
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("--stratisd-version should always succeed.")

    def testStratisLogLevel(self):
        """
        Getting log level should just succeed.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--stratisd-log-level']
            subprocess.check_call(command_line)
        except subprocess.CalledProcessError:
            self.fail("--stratisd-log-level should always succeed.")

    def testStratisNoOptions(self):
        """
        Exactly one option should be set, so this should fail.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU
            subprocess.check_call(command_line)
            self.fail('stratis with no option must fail')
        except subprocess.CalledProcessError:
            pass

    def testStratisTwoOptons(self):
        """
        Exactly one option should be set, so this should fail.
        """
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               ['--stratisd-log-level', '--stratisd-version']
            subprocess.check_call(command_line)
            self.fail('stratis with more than one option must fail')
        except subprocess.CalledProcessError:
            pass
