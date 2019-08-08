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
Test 'create'.
"""

from dbus_client_gen import DbusClientUniqueResultError

from stratis_cli._errors import StratisCliActionError

from .._misc import device_name_list
from .._misc import RUNNER
from .._misc import SimTestCase

_DEVICE_STRATEGY = device_name_list(1)


class AddDataTestCase(SimTestCase):
    """
    Test adding devices to a non-existant pool.
    """

    _MENU = ["--propagate", "pool", "add-data"]
    _POOLNAME = "deadpool"

    def testAdd(self):
        """
        Adding the devices must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, DbusClientUniqueResultError)


class AddCacheTestCase(SimTestCase):
    """
    Test adding devices to a non-existant pool.
    """

    _MENU = ["--propagate", "pool", "add-cache"]
    _POOLNAME = "deadpool"

    def testAdd(self):
        """
        Adding the devices must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, DbusClientUniqueResultError)
