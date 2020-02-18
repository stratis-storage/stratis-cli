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
# isort: STDLIB
from os import environ

# isort: THIRDPARTY
import dbus

# isort: FIRSTPARTY
from dbus_python_client_gen import DPClientInvocationError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes, handle_error
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

    def testLowTimeout(self):
        """
        Getting version with low timeout variable should fail.
        """
        environ["STRATIS_DBUS_TIMEOUT"] = "0"
        command_line = self._MENU + ["version"]

        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)

        exception = context.exception
        cause = exception.__cause__
        self.assertIsInstance(cause, DPClientInvocationError)
        self.assertIsInstance(cause.__cause__, dbus.exceptions.DBusException)
        self.assertEqual(
            cause.__cause__.get_dbus_name(), "org.freedesktop.DBus.Error.NoReply"
        )

        with self.assertRaises(SystemExit):
            handle_error(exception)


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
