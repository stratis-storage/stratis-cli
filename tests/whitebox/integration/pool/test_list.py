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
Test 'list'.
"""

# isort: STDLIB
from uuid import uuid4

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._actions._connection import get_object
from stratis_cli._actions._constants import TOP_OBJECT
from stratis_cli._errors import StratisCliResourceNotFoundError

from .._keyutils import RandomKeyTmpFile
from .._misc import (
    RUNNER,
    TEST_RUNNER,
    SimTestCase,
    device_name_list,
    get_pool,
    stop_pool,
)

_DEVICE_STRATEGY = device_name_list(1)

_ERROR = StratisCliErrorCodes.ERROR


class ListTestCase(SimTestCase):
    """
    Test 'list'.
    """

    _MENU = ["--propagate", "pool", "list"]

    def test_list(self):
        """
        List should just succeed, even though there is nothing to list.
        """
        command_line = self._MENU
        TEST_RUNNER(command_line)

    def test_list_default(self):
        """
        Test default listing action when "list" is not specified.

        List should just succeed, even though there is nothing to list.
        """
        command_line = self._MENU[:-1]
        TEST_RUNNER(command_line)


class List2TestCase(SimTestCase):
    """
    Test 'list' with something actually to list.
    """

    _MENU = ["--propagate", "pool", "list"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_list(self):
        """
        List should just succeed.
        """
        command_line = self._MENU
        TEST_RUNNER(command_line)

    def test_list_unhyphenated(self):
        """
        Test listing with unhyphenated-uuids flag
        """
        command_line = ["--unhyphenated-uuids"] + self._MENU
        TEST_RUNNER(command_line)

    def test_list_default(self):
        """
        Test default listing action when "list" is not specified.
        """
        command_line = self._MENU[:-1]
        TEST_RUNNER(command_line)

    def test_list_with_cache(self):
        """
        Test listing a pool with a cache. The purpose is to verify that
        strings representing boolean values with a True value are handled.
        """
        command_line = ["pool", "init-cache", self._POOLNAME] + _DEVICE_STRATEGY()
        TEST_RUNNER(command_line)
        command_line = self._MENU
        TEST_RUNNER(command_line)

    def test_list_bogus_uuid(self):
        """
        Test listing a bogus stopped pool.
        """
        command_line = self._MENU + [f"--uuid={uuid4()}"]
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)

    def test_list_with_uuid(self):
        """
        Test detailed list view for a specific uuid.
        """
        # pylint: disable=import-outside-toplevel
        # isort: LOCAL
        from stratis_cli._actions._data import MOPool

        proxy = get_object(TOP_OBJECT)

        mopool = MOPool(get_pool(proxy, self._POOLNAME)[1])
        command_line = self._MENU + [f"--uuid={mopool.Uuid()}"]
        TEST_RUNNER(command_line)


class List3TestCase(SimTestCase):
    """
    Test listing stopped pools.
    """

    _MENU = ["--propagate", "pool", "list", "--stopped"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator. Create a pool.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_list(self):
        """
        Test listing all with a stopped pool.
        """
        command_line = ["pool", "stop", self._POOLNAME]
        RUNNER(command_line)
        TEST_RUNNER(self._MENU)

    def test_list_empty(self):
        """
        Test listing when there are no stopped pools.
        """
        TEST_RUNNER(self._MENU)

    def test_list_specific(self):
        """
        Test listing a specific stopped pool.
        """

        pool_uuid = stop_pool(self._POOLNAME)

        command_line = self._MENU + [f"--uuid={pool_uuid}"]
        TEST_RUNNER(command_line)

    def test_list_bogus(self):
        """
        Test listing a bogus stopped pool.
        """
        command_line = self._MENU + [f"--uuid={uuid4()}"]
        self.check_error(StratisCliResourceNotFoundError, command_line, _ERROR)


class List4TestCase(SimTestCase):
    """
    Test listing stopped pools that have been encrypted.
    """

    _MENU = ["--propagate", "pool", "list", "--stopped"]
    _POOLNAME = "deadpool"
    _KEY_DESC = "keydesc"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator. Create a pool.
        """
        super().setUp()

        with RandomKeyTmpFile() as fname:
            command_line = [
                "--propagate",
                "key",
                "set",
                "--keyfile-path",
                fname,
                self._KEY_DESC,
            ]
            RUNNER(command_line)

        command_line = [
            "--propagate",
            "pool",
            "create",
            "--key-desc",
            self._KEY_DESC,
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_list(self):
        """
        Test listing all with a stopped pool.
        """
        command_line = ["pool", "stop", self._POOLNAME]
        RUNNER(command_line)
        TEST_RUNNER(self._MENU)
