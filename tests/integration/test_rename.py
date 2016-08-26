"""
Test 'rename'.
"""

import unittest

from stratis_cli._main import run
from stratis_cli._errors import StratisCliRuntimeError

from ._misc import Service


@unittest.skip("Wating for Rename")
class Rename1TestCase(unittest.TestCase):
    """
    Test 'rename' when pool is non-existant.
    """
    _MENU = ['rename']
    _POOLNAME = 'deadpool'
    _NEW_POOLNAME = 'livepool'

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

    def testRename(self):
        """
        This should fail because original name does not exist.
        """
        command_line = self._MENU + [self._POOLNAME] + [self._NEW_POOLNAME]
        with self.assertRaises(StratisCliRuntimeError):
            any(run(command_line))
