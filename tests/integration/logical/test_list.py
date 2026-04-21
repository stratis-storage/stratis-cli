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
Test 'list'.
"""
# isort: STDLIB
from unittest.mock import patch
from xml.etree import ElementTree

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientMissingPropertyError, DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes

from .._misc import (
    RUNNER,
    TEST_RUNNER,
    SimTestCase,
    device_name_list,
    split_device_list,
)

_DEVICE_STRATEGY = device_name_list(1)


class ListTestCase(SimTestCase):
    """
    Test listing a volume for a non-existent pool.
    """

    _MENU = ["--propagate", "filesystem", "list"]
    _POOLNAME = "deadpool"

    def test_list(self):
        """
        Listing the volume must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME]
        self.check_error(
            DbusClientUniqueResultError, command_line, StratisCliErrorCodes.ERROR
        )


class List2TestCase(SimTestCase):
    """
    Test listing volumes in an existing pool with no volumes.
    """

    _MENU = ["--propagate", "filesystem", "list"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create"] + [self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_list(self):
        """
        Listing the volumes in an empty pool should succeed.
        """
        command_line = self._MENU + [self._POOLNAME]
        TEST_RUNNER(command_line)


class List4TestCase(SimTestCase):
    """
    Test listing volumes in an existing pool with some volumes.
    """

    _POOLNAME = "deadpool"
    _VOLUMES = ["livery", "liberty", "library"]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        command_line = ["filesystem", "create", self._POOLNAME, self._VOLUMES[0]]
        RUNNER(command_line)
        command_line = ["filesystem", "create", self._POOLNAME, self._VOLUMES[1]]
        RUNNER(command_line)
        command_line = ["filesystem", "create", self._POOLNAME, self._VOLUMES[2]]
        RUNNER(command_line)

    def test_list(self):
        """
        Listing multiple volumes in a non-empty pool should succeed.
        """
        command_line = ["--propagate", "filesystem", "list", self._POOLNAME]
        TEST_RUNNER(command_line)

    def test_list_unhyphenated(self):
        """
        Listing multiple volumes with unhyphenated uuids in a non-empty pool should succeed.
        """
        command_line = [
            "--unhyphenated-uuids",
            "--propagate",
            "filesystem",
            "list",
            self._POOLNAME,
        ]
        TEST_RUNNER(command_line)


class List5TestCase(SimTestCase):
    """
    Test correctness of alternative list options.
    """

    _POOLNAMES = ["deadpool", "otherpool", "emptypool"]
    _VOLUMES = ["livery", "liberty", "library"]
    _MENU = ["--propagate", "filesystem", "list"]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()

        num_pools = 3
        devices = device_name_list(num_pools, 10 * num_pools, True)()
        device_lists = split_device_list(devices, num_pools)

        command_line = ["pool", "create", self._POOLNAMES[0]] + device_lists[0]
        RUNNER(command_line)

        command_line = ["filesystem", "create", self._POOLNAMES[0], self._VOLUMES[0]]
        RUNNER(command_line)
        command_line = ["filesystem", "create", self._POOLNAMES[0], self._VOLUMES[1]]
        RUNNER(command_line)
        command_line = [
            "filesystem",
            "snapshot",
            self._POOLNAMES[0],
            self._VOLUMES[1],
            self._VOLUMES[2],
        ]
        RUNNER(command_line)
        command_line = ["pool", "create", self._POOLNAMES[1]] + device_lists[1]
        RUNNER(command_line)
        command_line = ["filesystem", "create", self._POOLNAMES[1], self._VOLUMES[2]]
        RUNNER(command_line)
        command_line = ["pool", "create", self._POOLNAMES[2]] + device_lists[2]
        RUNNER(command_line)

    def test_list_one(self):
        """
        Specifying a pool name should yield only filesystems for that pool.
        """
        command_line = self._MENU + [self._POOLNAMES[1]]
        TEST_RUNNER(command_line)

    def test_list_no_pool(self):
        """
        If pool name is not specified, all filesystems for all pools should
        be listed.
        """
        command_line = self._MENU
        TEST_RUNNER(command_line)

    def test_list_default(self):
        """
        filesystem or fs subcommand should default to listing all pools.
        """
        command_line = self._MENU[:-1]
        TEST_RUNNER(command_line)

        command_line = ["--propagate", "fs"]
        TEST_RUNNER(command_line)

    def test_list_fs_name(self):
        """
        Test list with pool and filesystem name.
        """
        command_line = self._MENU + [self._POOLNAMES[0], f"--name={self._VOLUMES[0]}"]
        TEST_RUNNER(command_line)

    def test_list_fs_name_pool_name_not_match(self):
        """
        Test list with pool and filesystem name not coinciding.
        """
        command_line = self._MENU + [self._POOLNAMES[1], f"--name={self._VOLUMES[0]}"]
        self.check_error(
            DbusClientUniqueResultError, command_line, StratisCliErrorCodes.ERROR
        )

    def test_list_fs_name_snapshot(self):
        """
        Test list detailed view of a snapshot to test printing of revert information.
        """
        command_line = self._MENU + [self._POOLNAMES[0], f"--name={self._VOLUMES[2]}"]
        TEST_RUNNER(command_line)


class List6TestCase(SimTestCase):
    """
    Test listing pools when properties have gone missing.
    """

    _MENU = ["--propagate", "filesystem", "list"]
    _POOLNAME = "deadpool"
    _VOLUMES = ["livery", "liberty", "library"]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator. Create a pool.
        """
        super().setUp()

        command_line = [
            "--propagate",
            "pool",
            "create",
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        for fsname in self._VOLUMES[:2]:
            command_line = ["filesystem", "create", self._POOLNAME, fsname]
            RUNNER(command_line)

        command_line = [
            "filesystem",
            "snapshot",
            self._POOLNAME,
            self._VOLUMES[1],
            self._VOLUMES[2],
        ]
        RUNNER(command_line)

    def test_dropping_properties(self):
        """
        Verify no exception thrown if any of filesystem properties are dropped.

        However, avoid dropping Pool, Name, and Uuid properties, because
        lookup will fail in that case.
        """
        # isort: LOCAL
        import stratis_cli  # pylint: disable=import-outside-toplevel
        from stratis_cli import _actions  # pylint: disable=import-outside-toplevel

        # pylint: disable=import-outside-toplevel,protected-access
        from stratis_cli._actions._introspect import (
            SPECS,
        )

        filesystem_spec = SPECS[_actions._constants.FILESYSTEM_INTERFACE]
        spec = ElementTree.fromstring(filesystem_spec)

        for property_name in [
            prop.attrib["name"]
            for prop in spec.findall("./property")
            if not (prop.attrib["name"] in ("Pool", "Name", "Uuid"))
        ]:
            with patch.object(
                # pylint: disable=protected-access
                stratis_cli._actions._data.MOFilesystem,  # pyright: ignore
                property_name,
                autospec=True,
                side_effect=DbusClientMissingPropertyError(
                    "oops",
                    stratis_cli._actions._constants.FILESYSTEM_INTERFACE,  # pyright: ignore
                    property_name,
                ),
            ):
                for options in [
                    [self._POOLNAME],
                    [self._POOLNAME, f"--name={self._VOLUMES[0]}"],
                    [self._POOLNAME, f"--name={self._VOLUMES[1]}"],
                    [self._POOLNAME, f"--name={self._VOLUMES[2]}"],
                ]:
                    with self.subTest(
                        property_name=property_name,
                        options=options,
                    ):
                        TEST_RUNNER(self._MENU + options)
