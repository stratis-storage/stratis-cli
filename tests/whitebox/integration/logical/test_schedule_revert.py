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
Test 'schedule-revert'.
"""

# isort: FIRSTPARTY
from dbus_python_client_gen import DPClientInvocationError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliFsMergeScheduledChangeError

from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(1)
_ERROR = StratisCliErrorCodes.ERROR


class FsScheduleRevertTestCase(SimTestCase):
    """
    Test scheduling a revert for a filesystem.
    """

    _MENU = ["--propagate", "filesystem", "schedule-revert"]
    _POOLNAME = "pool"
    _FSNAME = "nofs"
    _SNAPNAME = "snofs"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        command_line = [
            "filesystem",
            "create",
            self._POOLNAME,
            self._FSNAME,
        ]
        RUNNER(command_line)

        command_line = [
            "filesystem",
            "snapshot",
            self._POOLNAME,
            self._FSNAME,
            self._SNAPNAME,
        ]
        RUNNER(command_line)

    def test_schedule_revert_twice(self):
        """
        Scheduling a revert twice should fail.
        """
        command_line = self._MENU + [
            self._POOLNAME,
            self._SNAPNAME,
        ]
        RUNNER(command_line)
        self.check_error(StratisCliFsMergeScheduledChangeError, command_line, _ERROR)

    def test_schedule_revert_once(self):
        """
        Scheduling a revert once should succeed.
        """
        command_line = self._MENU + [self._POOLNAME, self._SNAPNAME]
        TEST_RUNNER(command_line)

    def test_schedule_revert_on_filesystem_without_origin(self):
        """
        Scheduling a revert on a filesystem without an origin should fail.
        """
        command_line = self._MENU + [
            self._POOLNAME,
            self._FSNAME,
        ]
        self.check_error(DPClientInvocationError, command_line, _ERROR)
