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
Test D-Bus Timeout Environment Variable
"""
# isort: STDLIB
from os import environ

# isort: THIRDPARTY
import dbus

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliActionError

from .._misc import RUNNER, SimTestCase, handle_error

_ERROR = StratisCliErrorCodes.ERROR


class StratisTimeoutCase(SimTestCase):
    """
    Test stratis D-Bus timeout
    """

    _MENU = ["--propagate", "daemon"]

    def testLowTimeout(self):
        """
        Getting version with low timeout variable should fail.
        The cause is the second from the top level exception.
        """
        environ["STRATIS_DBUS_TIMEOUT"] = "0"
        command_line = self._MENU + ["version"]

        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)

        exception = context.exception
        cause = exception.__cause__.__cause__
        self.assertIsInstance(cause, dbus.exceptions.DBusException)

        with self.assertRaises(SystemExit) as final_err:
            handle_error(exception)

        final_code = final_err.exception.code
        self.assertEqual(final_code, _ERROR)
