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
Test 'add'.
"""

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import (
    StratisCliEngineError,
    StratisCliInUseOtherTierError,
    StratisCliInUseSameTierError,
    StratisCliPartialChangeError,
)

from .._misc import RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(1, 1)
_DEVICE_STRATEGY_2 = device_name_list(2, 2)
_ERROR = StratisCliErrorCodes.ERROR


class AddDataTestCase(SimTestCase):
    """
    Test adding devices to a non-existant pool.
    """

    _MENU = ["--propagate", "pool", "add-data"]
    _POOLNAME = "deadpool"

    def test_add(self):
        """
        Adding the devices must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)


class AddCacheTestCase(SimTestCase):
    """
    Test adding cache devices before initializing cache.
    """

    _MENU = ["--propagate", "pool", "add-cache"]
    _POOLNAME = "deadpool"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_add(self):
        """
        Adding the devices must fail since the cache is not initialized.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        self.check_error(StratisCliEngineError, command_line, _ERROR)


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

    def test_add_data(self):
        """
        Test that adding new devices to data tier succeeds.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_add_data_again(self):
        """
        Test that trying to add the same devices twice results in an
        exception.
        There are 0 target resources that would change.
        There is 1 target resource that would not change.
        """
        command_line = self._MENU + [self._POOLNAME] + self._DEVICES
        self.check_error(StratisCliPartialChangeError, command_line, _ERROR)

    def test_add_data_cache(self):
        """
        Test that adding 1 data device that is already in the cache tier raises
        an exception.
        """
        devices = _DEVICE_STRATEGY()
        command_line = (
            ["--propagate", "pool", "init-cache"] + [self._POOLNAME] + devices
        )
        RUNNER(command_line)
        self.check_error(
            StratisCliInUseOtherTierError,
            self._MENU + [self._POOLNAME] + devices,
            _ERROR,
        )

    def test_add_data_cache_2(self):
        """
        Test that adding multiple (2) data devices that are already in the cache tier raises
        an exception.
        """
        devices = _DEVICE_STRATEGY_2()
        command_line = (
            ["--propagate", "pool", "init-cache"] + [self._POOLNAME] + devices
        )
        RUNNER(command_line)
        self.check_error(
            StratisCliInUseOtherTierError,
            self._MENU + [self._POOLNAME] + devices,
            _ERROR,
        )


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

    def test_add_data(self):
        """
        Test that adding the same devices to the data tier in a different pool fails.
        """
        command_line = self._MENU + [self._POOLNAME] + self._SECOND_DEVICES
        self.check_error(StratisCliInUseSameTierError, command_line, _ERROR)


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
        command_line = [
            "--propagate",
            "pool",
            "init-cache",
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_add_cache(self):
        """
        Test that adding new devices to cache tier succeeds.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_add_cache_again(self):
        """
        Test that trying to add the same devices twice results in an
        exception.
        There are 0 target resources that would change.
        There is 1 target resource that would not change.
        """
        devices = _DEVICE_STRATEGY()
        command_line = self._MENU + [self._POOLNAME] + devices
        RUNNER(command_line)
        self.check_error(StratisCliPartialChangeError, command_line, _ERROR)

    def test_add_cache_data(self):
        """
        Test that adding 1 cache device that is already in the data tier raises
        an exception.
        """
        command_line = self._MENU + [self._POOLNAME] + self._DEVICES
        self.check_error(StratisCliInUseOtherTierError, command_line, _ERROR)


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
        command_line = [
            "--propagate",
            "pool",
            "init-cache",
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_add_cache_data(self):
        """
        Test that adding multiple (2) cache devices that are already in the data tier raises
        an exception.
        """
        command_line = self._MENU + [self._POOLNAME] + self._DEVICES_2
        self.check_error(StratisCliInUseOtherTierError, command_line, _ERROR)
