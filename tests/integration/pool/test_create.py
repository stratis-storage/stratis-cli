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

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import (
    StratisCliEngineError,
    StratisCliInUseSameTierError,
    StratisCliNameConflictError,
    StratisCliUserError,
)

from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(1)
_DEVICE_STRATEGY_2 = device_name_list(2)
_ERROR = StratisCliErrorCodes.ERROR


class CreateTestCase(SimTestCase):
    """
    Test create with relative paths
    """

    _MENU = ["--propagate", "pool", "create"]

    def test_relative_paths(self):
        """
        Verify that no assertion is thrown if path arguments are relative.
        """
        command_line = self._MENU + [
            "some_pool",
            "../dev",
            "./fake",
            "/abc",
        ]
        TEST_RUNNER(command_line)


class Create3TestCase(SimTestCase):
    """
    Test 'create' on name collision.
    """

    _MENU = ["--propagate", "pool", "create"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        self.devices = _DEVICE_STRATEGY()
        command_line = ["pool", "create", self._POOLNAME] + self.devices
        RUNNER(command_line)

    def test_create_same_devices(self):
        """
        Create should fail with a StratisCliNameConflictError trying to create
        new pool with the same devices and the same name as previous.
        """
        command_line = self._MENU + [self._POOLNAME] + self.devices
        self.check_error(StratisCliNameConflictError, command_line, _ERROR)

    def test_create_different_devices(self):
        """
        Create should fail with a StratisCliNameConflictError trying to create
        new pool with different devices and the same name as previous.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        self.check_error(StratisCliNameConflictError, command_line, _ERROR)


class Create4TestCase(SimTestCase):
    """
    Test adding data devices to two pools.
    """

    _POOLNAME_1 = "deadpool1"
    _POOLNAME_2 = "deadpool2"
    _MENU = ["--propagate", "pool", "create"]
    _DEVICES = _DEVICE_STRATEGY_2()

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME_1] + self._DEVICES
        RUNNER(command_line)

    def test_create_same_devices(self):
        """
        Test that creating two pools with different names and the same devices raises
        a StratisCliInUseSameTierError exception.
        """
        command_line = self._MENU + [self._POOLNAME_2] + self._DEVICES
        self.check_error(StratisCliInUseSameTierError, command_line, _ERROR)


class Create5TestCase(SimTestCase):
    """
    Test creating with Clevis options.
    """

    _POOLNAME = "deadpool1"
    _MENU = ["--propagate", "pool", "create"]
    _DEVICES = _DEVICE_STRATEGY_2()

    def test_create_tpm(self):
        """
        Test that creating with tpm2 does something reasonable.
        """
        command_line = self._MENU + [self._POOLNAME] + self._DEVICES + ["--clevis=tpm2"]
        TEST_RUNNER(command_line)

    def test_create_tang_1(self):
        """
        Test that creating with tang does something reasonable.
        """
        command_line = (
            self._MENU
            + [self._POOLNAME]
            + self._DEVICES
            + ["--clevis=tang", "--trust-url", "--tang-url=http"]
        )
        TEST_RUNNER(command_line)

    def test_create_tang_2(self):
        """
        Test that creating with tang does something reasonable.
        """
        command_line = (
            self._MENU
            + [self._POOLNAME]
            + self._DEVICES
            + ["--clevis=tang", "--thumbprint=print", "--tang-url=http"]
        )
        TEST_RUNNER(command_line)


class Create6TestCase(SimTestCase):
    """
    Test create with --no-overprovision flag set.
    """

    _MENU = ["--propagate", "pool", "create"]
    _DEVICES = _DEVICE_STRATEGY()
    _POOLNAME = "thispool"

    def test_no_overprovision(self):
        """
        Test create with no overprovisioning.
        """
        command_line = (
            self._MENU + [self._POOLNAME] + self._DEVICES + ["--no-overprovision"]
        )
        TEST_RUNNER(command_line)


class Create7TestCase(SimTestCase):
    """
    Test create with integrity options.
    """

    _MENU = ["--propagate", "pool", "create"]
    _DEVICES = _DEVICE_STRATEGY()
    _POOLNAME = "thispool"

    def test_invalid_journal_size(self):
        """
        Test creating with an invalid journal size.
        """
        command_line = (
            self._MENU + [self._POOLNAME] + self._DEVICES + ["--journal-size=131079KiB"]
        )
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_too_large_journal_size(self):
        """
        Test creating with a journal size that is too large for its D-Bus type.
        """
        command_line = (
            self._MENU
            + [self._POOLNAME]
            + self._DEVICES
            + ["--journal-size=18446744073709551616B"]
        )
        self.check_error(StratisCliUserError, command_line, _ERROR)
