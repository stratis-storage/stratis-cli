"""
Test 'create'.
"""

import unittest

from stratis_cli._main import run

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
        command_line = self._MENU + ['--version']
        all(run(command_line))

    def testStratisLogLevel(self):
        """
        Getting log level should just succeed.
        """
        command_line = self._MENU + ['--log-level']
        all(run(command_line))

    def testStratisNoOptions(self):
        """
        Exactly one option should be set, so this should fail.
        """
        command_line = self._MENU
        with self.assertRaises(SystemExit):
            all(run(command_line))

    def testStratisTwoOptons(self):
        """
        Exactly one option should be set, so this should fail.
        """
        command_line = self._MENU + ['--log-level', '--version']
        with self.assertRaises(SystemExit):
            all(run(command_line))
