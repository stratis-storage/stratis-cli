# Copyright 2022 Red Hat, Inc.
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
Test 'report'.
"""
# isort: STDLIB
from uuid import uuid4

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes

from .._misc import RUNNER, SimTestCase, device_name_list

_ERROR = StratisCliErrorCodes.ERROR
_DEVICE_STRATEGY = device_name_list(1, 1)


class ReportTestCase(SimTestCase):
    """
    Test 'report' on a sim pool.
    """

    _MENU = ["--propagate", "pool", "report"]
    _POOLNAME = "poolname"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_call_bad_uuid(self):
        """
        Test bad uuid
        """
        command_line = self._MENU + ["--uuid", str(uuid4())]
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)

    def test_report_bad_name(self):
        """
        Test bad name.
        """
        command_line = self._MENU + [
            "--name",
            "noone",
        ]
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)
