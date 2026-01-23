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
Test 'debug'.
"""
# isort: STDLIB
from uuid import uuid4

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes

from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_ERROR = StratisCliErrorCodes.ERROR
_DEVICE_STRATEGY = device_name_list(1, 1)


class DebugTestCase(SimTestCase):
    """
    Test 'debug' on a sim pool.
    """

    _MENU = ["--propagate", "blockdev", "debug"]
    _POOLNAME = "poolname"
    _DEVICES = _DEVICE_STRATEGY()

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + self._DEVICES
        RUNNER(command_line)

    def test_lookup_bad_uuid(self):
        """
        Test bad uuid
        """
        command_line = self._MENU + ["get-object-path", "--uuid", str(uuid4())]
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)

    def test_lookup_uuid(self):
        """
        Test good uuid
        """

        # isort: LOCAL
        # pylint: disable=import-outside-toplevel
        from stratis_cli._actions._connection import get_object
        from stratis_cli._actions._constants import TOP_OBJECT
        from stratis_cli._actions._data import BLOCKDEV_GEN, OBJECT_MANAGER_GEN

        ObjectManager = OBJECT_MANAGER_GEN.dp_class()
        (MODev, devs) = (BLOCKDEV_GEN.mo(), BLOCKDEV_GEN.query_builder())

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (_, info) = next(devs().search(managed_objects))
        uuid = MODev(info).Uuid()

        command_line = self._MENU + ["get-object-path", "--uuid", uuid]
        TEST_RUNNER(command_line)
