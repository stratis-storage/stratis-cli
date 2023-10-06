# Copyright 2023 Red Hat, Inc.
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
Test 'set-size-limit'.
"""

# isort: FIRSTPARTY
from dbus_python_client_gen import DPClientInvocationError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliFsSizeLimitChangeError

from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(1)
_ERROR = StratisCliErrorCodes.ERROR


class SetSizeLimitTestCase(SimTestCase):
    """
    Test setting the size limit for a filesystem.
    """

    _MENU = ["--propagate", "filesystem", "set-size-limit"]
    _POOLNAME = "pool"
    _FSNAME = "nofs"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        command_line = ["filesystem", "create", self._POOLNAME, self._FSNAME]
        RUNNER(command_line)

    def test_set_size_limit_twice(self):
        """
        Setting the size limit to the existing size limit must fail.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, "2TiB"]
        RUNNER(command_line)
        self.check_error(StratisCliFsSizeLimitChangeError, command_line, _ERROR)

    def test_set_size_limit_current_twice(self):
        """
        Use "current" to set the size limit to the same value twice.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, "current"]
        RUNNER(command_line)
        self.check_error(StratisCliFsSizeLimitChangeError, command_line, _ERROR)

    def test_set_size_limit_exact(self):
        """
        Setting the filesystem size limit to exactly 1 TiB should succeed.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, "1TiB"]
        TEST_RUNNER(command_line)

    def test_set_size_limit_double(self):
        """
        Setting the filesystem size limit to double the size should succeed.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, "2TiB"]
        TEST_RUNNER(command_line)

    def test_set_size_limit_below(self):
        """
        Setting the size limit to less than the current size should fail.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, "512GiB"]
        self.check_error(DPClientInvocationError, command_line, _ERROR)

    def test_set_size_limit_current(self):
        """
        Set the size limit to the current filesystem size, whatever that is.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, "current"]
        TEST_RUNNER(command_line)
