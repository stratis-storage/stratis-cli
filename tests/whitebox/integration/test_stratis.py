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

from ._misc import RUNNER, TEST_RUNNER, RunTestCase, SimTestCase

_ERROR = StratisCliErrorCodes.ERROR


class StratisTestCase(SimTestCase):
    """
    Test meta information about stratisd.
    """

    _MENU = ["--propagate", "daemon"]

    def test_stratis_version(self):
        """
        Getting version should just succeed.
        """
        command_line = self._MENU + ["version"]
        TEST_RUNNER(command_line)

    def test_stratis_redundancy(self):
        """
        Getting redundancy should just succeed.
        """
        command_line = self._MENU + ["redundancy"]
        TEST_RUNNER(command_line)


class PropagateTestCase(RunTestCase):
    """
    Verify correct operation of --propagate flag.
    """

    def test_propagate(self):
        """
        If propagate is set, the expected exception will propagate.
        """
        command_line = ["--propagate", "daemon", "version"]
        self.check_error(dbus.exceptions.DBusException, command_line, _ERROR)

    def test_not_propagate(self):
        """
        If propagate is not set, the exception will be SystemExit.
        """
        command_line = ["daemon", "version"]
        with self.assertRaises(SystemExit):
            RUNNER(command_line)
