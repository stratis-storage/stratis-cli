# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Test 'stratisd'.
"""

import unittest

import dbus

from stratis_cli._errors import StratisCliActionError

from ._misc import RUNNER
from ._misc import SimTestCase


class StratisTestCase(SimTestCase):
    """
    Test meta information about stratisd.
    """

    _MENU = ["--propagate", "daemon"]

    def testStratisVersion(self):
        """
        Getting version should just succeed.
        """
        command_line = self._MENU + ["version"]
        RUNNER(command_line)

    def testStratisRedundancy(self):
        """
        Getting redundancy should just succeed.
        """
        command_line = self._MENU + ["redundancy"]
        RUNNER(command_line)

    def testStratisNoOptions(self):
        """
        Exactly one option should be set, this should succeed, but print help.
        """
        command_line = self._MENU
        RUNNER(command_line)

    def testStratisTwoOptions(self):
        """
        Exactly one option should be set, so this should fail,
        but only because redundancy accepts no arguments.
        """
        command_line = self._MENU + ["redundancy", "version"]
        with self.assertRaises(SystemExit):
            RUNNER(command_line)


class PropagateTestCase(unittest.TestCase):
    """
    Verify correct operation of --propagate flag.
    """

    def testPropagate(self):
        """
        If propagate is set, the expected exception will propagate.
        """
        command_line = ["--propagate", "daemon", "version"]
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, dbus.exceptions.DBusException)

    def testNotPropagate(self):
        """
        If propagate is not set, the exception will be SystemExit.
        """
        command_line = ["daemon", "version"]
        with self.assertRaises(SystemExit):
            RUNNER(command_line)


class ErrorHandlingTestCase(SimTestCase):
    """
    Test error-handling behavior when --propagate is not set.
    """

    def testErrorOnMissingFilesystem(self):
        """
        Test that listing filesystems for a non-existent pool results in early
        exit.
        """
        command_line = ["filesystem", "list", "not_existing"]

        # if exceptions are propagated then a Stratis error is caught
        with self.assertRaises(StratisCliActionError):
            RUNNER(["--propagate"] + command_line)

        # If instead the exception chain is handed off to handle_error,
        # the exception is recognized, an error message is generated,
        # and the program exits with the message via SystemExit.
        with self.assertRaises(SystemExit) as context:
            RUNNER(command_line)
        exit_code = context.exception.code
        self.assertNotEqual(exit_code, 0)
        self.assertIsNotNone(exit_code)
