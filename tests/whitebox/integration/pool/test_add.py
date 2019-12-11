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

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli._errors import (
    StratisCliActionError,
    StratisCliInUseOtherTierError,
    StratisCliInUseSameTierError,
    StratisCliPartialChangeError,
)

from .._misc import RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(1, 1)
_DEVICE_STRATEGY_2 = device_name_list(2, 2)


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
        There are 0 target resources that would change.
        There is 1 target resource that would not change.
        """
        command_line = self._MENU + [self._POOLNAME] + self._DEVICES
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliPartialChangeError)

    def testAddDataCache(self):
        """
        Test that adding 1 data device that is already in the cache tier raises
        an exception.
        """
        devices = _DEVICE_STRATEGY()
        command_line = ["--propagate", "pool", "add-cache"] + [self._POOLNAME] + devices
        RUNNER(command_line)
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(self._MENU + [self._POOLNAME] + devices)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliInUseOtherTierError)
        self.assertNotEqual(str(cause), "")

    def testAddDataCache2(self):
        """
        Test that adding multiple (2) data devices that are already in the cache tier raises
        an exception.
        """
        devices = _DEVICE_STRATEGY_2()
        command_line = ["--propagate", "pool", "add-cache"] + [self._POOLNAME] + devices
        RUNNER(command_line)
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(self._MENU + [self._POOLNAME] + devices)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliInUseOtherTierError)
        self.assertNotEqual(str(cause), "")


class AddDataTestCase2(SimTestCase):
    """
    Test adding data devices where the devices are already in the data tier
    of another pool.
    """

    _POOLNAME = "deadpool"
    _SECOND_POOLNAME = "deadpool2"
    _MENU = ["--propagate", "pool", "add-data"]
    _DEVICES = _DEVICE_STRATEGY()
    _SECOND_DEVICES = _DEVICE_STRATEGY()

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + self._DEVICES
        RUNNER(command_line)
        command_line = ["pool", "create", self._SECOND_POOLNAME] + self._SECOND_DEVICES
        RUNNER(command_line)

    def testAddData(self):
        """
        Test that adding the same devices to the data tier in a different pool fails.
        """
        command_line = self._MENU + [self._POOLNAME] + self._SECOND_DEVICES
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliInUseSameTierError)
        self.assertNotEqual(str(cause), "")


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
        There are 0 target resources that would change.
        There is 1 target resource that would not change.
        """
        devices = _DEVICE_STRATEGY()
        command_line = self._MENU + [self._POOLNAME] + devices
        RUNNER(command_line)
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliPartialChangeError)
        self.assertNotEqual(str(cause), "")

    def testAddCacheData(self):
        """
        Test that adding 1 cache device that is already in the data tier raises
        an exception.
        """
        command_line = self._MENU + [self._POOLNAME] + self._DEVICES
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliInUseOtherTierError)
        self.assertNotEqual(str(cause), "")


class AddCacheTestCase2(SimTestCase):
    """
    Test adding cache devices to an existing pool.
    """

    _POOLNAME = "deadpool"
    _MENU = ["--propagate", "pool", "add-cache"]
    _DEVICES_2 = _DEVICE_STRATEGY_2()

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + self._DEVICES_2
        RUNNER(command_line)

    def testAddCacheData(self):
        """
        Test that adding multiple (2) cache devices that are already in the data tier raises
        an exception.
        """
        command_line = self._MENU + [self._POOLNAME] + self._DEVICES_2
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliInUseOtherTierError)
        self.assertNotEqual(str(cause), "")
