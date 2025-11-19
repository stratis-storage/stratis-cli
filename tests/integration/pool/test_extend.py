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
Test 'extend-data'.
"""

# isort: STDLIB
from uuid import UUID, uuid4

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._actions._connection import get_object
from stratis_cli._actions._constants import TOP_OBJECT
from stratis_cli._errors import (
    StratisCliNoDeviceSizeChangeError,
    StratisCliPartialChangeError,
    StratisCliResourceNotFoundError,
)

from .._misc import RUNNER, SimTestCase, device_name_list, get_pool_blockdevs

_ERROR = StratisCliErrorCodes.ERROR
_DEVICE_STRATEGY = device_name_list(1, 1)


class ExtendDataTestCase(SimTestCase):
    """
    Test 'extend-data' on a sim pool.
    """

    _MENU = ["--propagate", "pool", "extend-data"]
    _POOLNAME = "poolname"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_bad_uuid(self):
        """
        Test trying to extend a device specifying a non-existent device UUID.
        """
        command_line = self._MENU + [self._POOLNAME, f"--device-uuid={uuid4()}"]
        self.check_error(StratisCliResourceNotFoundError, command_line, _ERROR)

    def test_no_uuid(self):
        """
        Test trying to extend a pool without specifying a UUID.
        """
        command_line = self._MENU + [self._POOLNAME]
        self.check_error(StratisCliNoDeviceSizeChangeError, command_line, _ERROR)

    def test_good_uuid(self):
        """
        Test trying to extend a device specifying an existing device UUID.
        """
        _, props = next(get_pool_blockdevs(get_object(TOP_OBJECT), self._POOLNAME))
        command_line = self._MENU + [
            self._POOLNAME,
            f"--device-uuid={UUID(props.Uuid())}",
        ]
        self.check_error(StratisCliPartialChangeError, command_line, _ERROR)
