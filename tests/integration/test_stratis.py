"""
Test 'create'.
"""

import subprocess
import unittest

from ._constants import _CLI

from ._misc import Service


class StratisTestCase(unittest.TestCase):
    """
    Test meta information about stratisd.
    """
    _MENU = ['stratis']

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
