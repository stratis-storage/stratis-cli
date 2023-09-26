# Copyright 2019 Red Hat, Inc.
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

from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(1)
_ERROR = StratisCliErrorCodes.ERROR


class RenameTestCase(SimTestCase):
    """
    Test renaming a filesystem in a pool.
    """

    _MENU = ["--propagate", "filesystem", "rename"]
    _POOLNAME = "deadpool"
    _FSNAME = "fs"
    _RENAMEFSNAME = "renamefs"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        command_line = ["filesystem", "create", self._POOLNAME, self._FSNAME]
        RUNNER(command_line)

    def test_rename(self):
        """
        Renaming the filesystem should succeed,
        because origin the pool and filesystem are available.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, self._RENAMEFSNAME]
        TEST_RUNNER(command_line)

    def test_same_name(self):
        """
        Renaming the filesystem must fail, because this performs no action.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, self._FSNAME]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)


class Rename1TestCase(SimTestCase):
    """
    Test 'rename' when pool is non-existent.
    """

    _MENU = ["--propagate", "filesystem", "rename"]
    _POOLNAME = "nopool"
    _FSNAME = "fs"
    _RENAMEFSNAME = "renamefs"

    def test_non_existent_pool(self):
        """
        Renaming the filesystem must fail, because the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, self._RENAMEFSNAME]

        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)

    def test_non_existent_pool_same_name(self):
        """
        Renaming the filesystem must fail, because the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, self._RENAMEFSNAME]
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)


class Rename2TestCase(SimTestCase):
    """
    Test renaming a non-existent filesystem.
    """

    _MENU = ["--propagate", "filesystem", "rename"]
    _POOLNAME = "pool"
    _FSNAME = "nofs"
    _RENAMEFSNAME = "renamefs"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_non_existent_filesystem(self):
        """
        Renaming the filesystem must fail, because filesystem does not exist.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, self._RENAMEFSNAME]
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)

    def test_non_existent_filesystem_same_name(self):
        """
        Renaming the filesystem must fail, because the filesystem does not exist.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, self._RENAMEFSNAME]
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)
