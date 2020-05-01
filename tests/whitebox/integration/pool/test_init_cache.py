# Copyright 2020 Red Hat, Inc.
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
Test 'init-cache'.
"""

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliEngineError, StratisCliPartialChangeError

from .._misc import RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(2)
_ERROR = StratisCliErrorCodes.ERROR


class InitCacheFailTestCase(SimTestCase):
    """
    Test 'init-cache' with two different lists of devices.

    'init-cache' should always fail if the cache is initialized twice with
    different devices.
    """

    _MENU = ["--propagate", "pool", "init-cache"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start stratisd and set up a pool.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_init_cache(self):
        """
        Test two initializations of the cache with two different device lists.

        Should fail.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        self.check_error(StratisCliEngineError, command_line, _ERROR)


class InitCacheFail2TestCase(SimTestCase):
    """
    Test 'init-cache' the same list of devices twice.

    'init-cache' should always fail if the cache is initialized twice with
    the same devices.
    """

    _MENU = ["--propagate", "pool", "init-cache"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start stratisd and set up a pool.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_init_cache(self):
        """
        Test two initializations of the cache with the same device list.

        Should fail.
        """
        devices = _DEVICE_STRATEGY()
        command_line = self._MENU + [self._POOLNAME] + devices
        RUNNER(command_line)
        self.check_error(StratisCliPartialChangeError, command_line, _ERROR)


class InitCacheFail3TestCase(SimTestCase):
    """
    Test 'init-cache' for a non-existant pool.
    """

    _MENU = ["--propagate", "pool", "init-cache"]
    _POOLNAME = "deadpool"

    def test_init_cache(self):
        """
        Intializing the cache must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        self.check_error(DbusClientUniqueResultError, command_line, _ERROR)


class InitCacheFail4TestCase(SimTestCase):
    """
    Test 'init-cache' for encrypted pool.
    """

    _MENU = ["--propagate", "pool", "init-cache"]
    _POOLNAME = "deadpool"

    def setUp(self):
        super().setUp()
        command_line = [
            "pool",
            "create",
            "--key-desc",
            "test-password",
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_init_cache(self):
        """
        Initializing the cache must fail since the pool is encrypted.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        self.check_error(StratisCliEngineError, command_line, _ERROR)


class InitCacheSuccessTestCase(SimTestCase):
    """
    Test 'init-cache' once.

    'init-cache' should succeed.
    """

    _MENU = ["--propagate", "pool", "init-cache"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start stratisd and set up a pool.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_init_cache(self):
        """
        Test an initialization of the cache with a device list.

        Should succeed.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)
