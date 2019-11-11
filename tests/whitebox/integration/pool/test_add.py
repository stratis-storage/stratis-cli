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
from stratis_cli._errors import StratisCliInUseError
from stratis_cli._errors import StratisCliPartialChangeError

from .._misc import RUNNER
from .._misc import SimTestCase
from .._misc import device_name_list

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


class AddDataTestCase1(SimTestCase):
    """
    Test adding devices to data tier of an existing pool.
    """

    _POOLNAME = "deadpool"
    _MENU = ["--propagate", "pool", "add-data"]
    _DEVICES = _DEVICE_STRATEGY()

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + self._DEVICES
        RUNNER(command_line)

    def testAddData(self):
        """
        Test that adding new devices to data tier succeeds.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def testAddDataAgain(self):
        """
        Test that trying to add the same devices twice results in an
        exception.
        """
        command_line = self._MENU + [self._POOLNAME] + self._DEVICES
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliPartialChangeError)

    def testAddDataCache(self):
        """
        Test that adding data devices that are already in the cache tier raises
        an exception.
        """
        devices = _DEVICE_STRATEGY()
        command_line = ["--propagate", "pool", "add-cache"] + [self._POOLNAME] + devices
        RUNNER(command_line)
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(self._MENU + [self._POOLNAME] + devices)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliInUseError)


class AddCacheTestCase1(SimTestCase):
    """
    Test adding cache devices to an existing pool.
    """

    _POOLNAME = "deadpool"
    _MENU = ["--propagate", "pool", "add-cache"]
    _DEVICES = _DEVICE_STRATEGY()

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + self._DEVICES
        RUNNER(command_line)

    def testAddCache(self):
        """
        Test that adding new devices to cache tier succeeds.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def testAddCacheAgain(self):
        """
        Test that trying to add the same devices twice results in an
        exception.
        """
        devices = _DEVICE_STRATEGY()
        command_line = self._MENU + [self._POOLNAME] + devices
        RUNNER(command_line)
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliPartialChangeError)

    def testAddCacheData(self):
        """
        Test that adding cache devices that are already in the data tier raises
        an exception.
        """
        command_line = self._MENU + [self._POOLNAME] + self._DEVICES
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliInUseError)
