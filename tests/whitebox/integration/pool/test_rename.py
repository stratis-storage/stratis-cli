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
Test 'rename'.
"""

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliNoChangeError

from .._misc import RUNNER, SimTestCase, TEST_RUNNER, device_name_list

_DEVICE_STRATEGY = device_name_list(1)
_ERROR = StratisCliErrorCodes.ERROR


class Rename1TestCase(SimTestCase):
    """
    Test 'rename' when pool is non-existant.
    """

    _MENU = ["--propagate", "pool", "rename"]
    _POOLNAME = "deadpool"
    _NEW_POOLNAME = "livepool"

    def test_rename(self):
        """
        This should fail because original name does not exist.
        """
        command_line = self._MENU + [self._POOLNAME, self._NEW_POOLNAME]
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)

    def test_same_name(self):
        """
        Renaming to itself will fail because the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME, self._POOLNAME]
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)


class Rename2TestCase(SimTestCase):
    """
    Test 'rename' when pool exists.
    """

    _MENU = ["--propagate", "pool", "rename"]
    _POOLNAME = "deadpool"
    _NEW_POOLNAME = "livepool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_rename(self):
        """
        This should succeed because pool exists.
        """
        command_line = self._MENU + [self._POOLNAME, self._NEW_POOLNAME]
        TEST_RUNNER(command_line)

    def test_same_name(self):
        """
        This should fail, because this performs no action.
        """
        command_line = self._MENU + [self._POOLNAME, self._POOLNAME]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)

    def test_non_existent_pool(self):
        """
        This should fail, because this pool is not there.
        """
        command_line = self._MENU + ["nopool", self._POOLNAME]
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)
