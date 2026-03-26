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
from unittest.mock import patch
from uuid import uuid4
from xml.etree import ElementTree  # nosect B405

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientMissingPropertyError, DbusClientUniqueResultError

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
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        TEST_RUNNER(self._MENU)

    def test_list_empty(self):
        """
        Test listing when there are no stopped pools.
        """
        TEST_RUNNER(self._MENU)

    def test_list_specific_uuid(self):
        """
        Test listing a specific stopped pool by uuid.
        """

        pool_uuid = stop_pool(self._POOLNAME)

        command_line = self._MENU + [f"--uuid={pool_uuid}"]
        TEST_RUNNER(command_line)

    def test_list_specific_name(self):
        """
        Test listing a specific stopped pool by name.
        """
        stop_pool(self._POOLNAME)

        command_line = self._MENU + [f"--name={self._POOLNAME}"]
        TEST_RUNNER(command_line)

    def test_list_bogus_uuid(self):
        """
        Test listing a bogus stopped pool by UUID.
        """
        command_line = self._MENU + [f"--uuid={uuid4()}"]
        self.check_error(StratisCliResourceNotFoundError, command_line, _ERROR)

    def test_list_unstopped__name(self):
        """
        Test listing a stopped pool by name, while not stopped.
        """
        command_line = self._MENU + [f"--name={self._POOLNAME}"]
        self.check_error(StratisCliResourceNotFoundError, command_line, _ERROR)


class List4TestCase(SimTestCase):
    """
    Test listing pools that have been encrypted with a key.
    """

    _MENU = ["--propagate", "pool", "list"]
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

    def test_list_stopped(self):
        """
        Test listing all with a stopped pool.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        TEST_RUNNER(self._MENU + ["--stopped"])

    def test_list_stopped_detail(self):
        """
        Test detailed view on a stopped pool.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        TEST_RUNNER(self._MENU + ["--stopped", f"--name={self._POOLNAME}"])

    def test_list_running(self):
        """
        Test list all running pools.
        """
        TEST_RUNNER(self._MENU)

    def test_list_detail(self):
        """
        Test detail view on running pool.
        """
        TEST_RUNNER(self._MENU + [f"--name={self._POOLNAME}"])


class List5TestCase(SimTestCase):
    """
    Test listing pools that have been encrypted with clevis.
    """

    _MENU = ["--propagate", "pool", "list"]
    _POOLNAME = "deadpool"

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
            "--clevis=tang",
            "--trust-url",
            "--tang-url=http",
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_list_stopped(self):
        """
        Test listing all with a stopped pool.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        TEST_RUNNER(self._MENU + ["--stopped"])

    def test_list_stopped_detail(self):
        """
        Test detailed view on a stopped pool.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        TEST_RUNNER(self._MENU + ["--stopped", f"--name={self._POOLNAME}"])

    def test_list_running(self):
        """
        Test list all running pools.
        """
        TEST_RUNNER(self._MENU)

    def test_list_detail(self):
        """
        Test detail view on running pool.
        """
        TEST_RUNNER(self._MENU + [f"--name={self._POOLNAME}"])


class List6TestCase(SimTestCase):
    """
    Test listing pools when properties have gone missing.
    """

    _MENU = ["--propagate", "pool", "list"]
    _POOLNAME = "deadpool"

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

    def test_dropping_properties(self):
        """
        Verify no exception thrown if any of pool properties are dropped.
        """
        # isort: LOCAL
        import stratis_cli  # pylint: disable=import-outside-toplevel
        from stratis_cli import _actions  # pylint: disable=import-outside-toplevel

        # pylint: disable=import-outside-toplevel,protected-access
        from stratis_cli._actions._introspect import (
            SPECS,
        )

        pool_spec = SPECS[_actions._constants.POOL_INTERFACE]
        spec = ElementTree.fromstring(pool_spec)  # nosec B314

        for property_name in [
            prop.attrib["name"] for prop in spec.findall("./property")
        ]:
            with patch.object(
                # pylint: disable=protected-access
                stratis_cli._actions._data.MOPool,  # pyright: ignore
                property_name,
                autospec=True,
                side_effect=DbusClientMissingPropertyError(
                    "oops",
                    stratis_cli._actions._constants.POOL_INTERFACE,  # pyright: ignore
                    property_name,
                ),
            ):
                for options in [[], [f"--name={self._POOLNAME}"]]:
                    with self.subTest(
                        property_name=property_name,
                        options=options,
                    ):
                        TEST_RUNNER(self._MENU + options)


class List7TestCase(SimTestCase):
    """
    Test listing pools when properties have gone missing and the pool is
    encrypted.
    """

    _MENU = ["--propagate", "pool", "list"]
    _POOLNAME = "deadpool"

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
            "--clevis=tang",
            "--trust-url",
            "--tang-url=http",
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_dropping_properties(self):
        """
        Verify no exception thrown if any of pool properties are dropped.
        """
        # isort: LOCAL
        import stratis_cli  # pylint: disable=import-outside-toplevel
        from stratis_cli import _actions  # pylint: disable=import-outside-toplevel

        # pylint: disable=import-outside-toplevel,protected-access
        from stratis_cli._actions._introspect import (
            SPECS,
        )

        pool_spec = SPECS[_actions._constants.POOL_INTERFACE]
        spec = ElementTree.fromstring(pool_spec)  # nosec B314

        for property_name in [
            prop.attrib["name"] for prop in spec.findall("./property")
        ]:
            with patch.object(
                # pylint: disable=protected-access
                stratis_cli._actions._data.MOPool,  # pyright: ignore
                property_name,
                autospec=True,
                side_effect=DbusClientMissingPropertyError(
                    "oops",
                    stratis_cli._actions._constants.POOL_INTERFACE,  # pyright: ignore
                    property_name,
                ),
            ):
                for options in [[], [f"--name={self._POOLNAME}"]]:
                    with self.subTest(
                        property_name=property_name,
                        options=options,
                    ):
                        TEST_RUNNER(self._MENU + options)
