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
Test 'snapshot'.
"""

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliActionError, StratisCliNoChangeError

from .._misc import RUNNER, SimTestCase, check_error, device_name_list

_DEVICE_STRATEGY = device_name_list(1)
ERROR = StratisCliErrorCodes.ERROR


class SnapshotTestCase(SimTestCase):
    """
    Test creating a snapshot of a filesystem in a pool.
    """

    _MENU = ["--propagate", "filesystem", "snapshot"]
    _POOLNAME = "deadpool"
    _SNAPNAME = "snapfs"
    _FSNAME = "fs"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)
        command_line = ["filesystem", "create", self._POOLNAME, self._FSNAME]
        RUNNER(command_line)

    def testSnapshot(self):
        """
        Creation of the snapshot should succeed since origin pool/filesytem is available.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, self._SNAPNAME]
        RUNNER(command_line)

    def testSameName(self):
        """
        Creation of the snapshot must fail, because this performs no action.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, self._FSNAME]
        check_error(
            self, StratisCliActionError, StratisCliNoChangeError, command_line, ERROR
        )


class Snapshot1TestCase(SimTestCase):
    """
    Test creating a snapshot w/out a pool.
    """

    _MENU = ["--propagate", "filesystem", "snapshot"]
    _POOLNAME = "nopool"
    _SNAPNAME = "snapfs"
    _FSNAME = "fs"

    def testCreation(self):
        """
        Creation of the snapshot must fail since specified pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, self._SNAPNAME]
        check_error(
            self,
            StratisCliActionError,
            DbusClientUniqueResultError,
            command_line,
            ERROR,
        )


class Snapshot2TestCase(SimTestCase):
    """
    Test creating a snapshot w/out a filesystem.
    """

    _MENU = ["--propagate", "filesystem", "snapshot"]
    _POOLNAME = "pool"
    _FSNAME = "fs"
    _SNAPNAME = "snapfs"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def testCreation(self):
        """
        Creation of the snapshot must fail since filesystem does not exist.
        """
        command_line = self._MENU + [self._POOLNAME, self._FSNAME, self._SNAPNAME]
        check_error(
            self,
            StratisCliActionError,
            DbusClientUniqueResultError,
            command_line,
            ERROR,
        )
