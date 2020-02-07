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

# isort: THIRDPARTY
import dbus

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliActionError

from ._misc import RUNNER, RunTestCase, SimTestCase

_ERROR = StratisCliErrorCodes.ERROR


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


class PropagateTestCase(RunTestCase):
    """
    Verify correct operation of --propagate flag.
    """

    def testPropagate(self):
        """
        If propagate is set, the expected exception will propagate.
        """
        command_line = ["--propagate", "daemon", "version"]
        self.check_error(dbus.exceptions.DBusException, command_line, _ERROR)

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
        self.check_system_exit(command_line, _ERROR)
