"""
Test 'rename'.
"""

import subprocess
import unittest

from ._constants import _CLI

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
        try:
            command_line = \
               ['python', _CLI] + \
               self._MENU + \
               [self._POOLNAME] + \
               [self._NEW_POOLNAME]
            subprocess.check_call(command_line)
            self.fail(
               "Should have failed because %s does not exist." % self._POOLNAME
            )
        except subprocess.CalledProcessError:
            pass
