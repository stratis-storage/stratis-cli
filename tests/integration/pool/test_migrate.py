# Copyright 2026 Red Hat, Inc.
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
Test 'migrate'.
"""

from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import (
    StratisCliEngineError,
    StratisCliResourceNotFoundError,
    StratisCliUserError,
)

from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(1)
_DEVICE_STRATEGY_2 = device_name_list(2)
_ERROR = StratisCliErrorCodes.ERROR


class MigrateTestCase(SimTestCase):
    """
    Test migrate with relative paths
    """

    _MENU = ["--propagate", "pool", "migrate"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        self.devices = _DEVICE_STRATEGY()
        command_line = ["pool", "create", self._POOLNAME] + self.devices
        RUNNER(command_line)

    def test_relative_paths(self):
        """
        Verify that no assertion is thrown if path arguments are relative.
        """
        command_line = self._MENU + [
            "--name",
            self._POOLNAME,
            "../dev",
            "./fake",
            "/abc",
        ]
        TEST_RUNNER(command_line)


class Migrate2TestCase(SimTestCase):
    """
    Test migrate with Clevis options.
    """

    _POOLNAME = "deadpool1"
    _MENU = ["--propagate", "pool", "migrate"]
    _DEVICES = _DEVICE_STRATEGY_2()

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + self._DEVICES
        RUNNER(command_line)

    def test_migrate_tpm(self):
        """
        Test that migrating with tpm2 does something reasonable.
        """
        new_devices = _DEVICE_STRATEGY_2()
        command_line = (
            self._MENU + ["--name", self._POOLNAME] + new_devices + ["--clevis=tpm2"]
        )
        TEST_RUNNER(command_line)

    def test_migrate_tang_1(self):
        """
        Test that migrating with tang does something reasonable.
        """
        new_devices = _DEVICE_STRATEGY_2()
        command_line = (
            self._MENU
            + ["--name", self._POOLNAME]
            + new_devices
            + ["--clevis=tang", "--trust-url", "--tang-url=http"]
        )
        TEST_RUNNER(command_line)

    def test_migrate_tang_2(self):
        """
        Test that migrating with tang does something reasonable.
        """
        new_devices = _DEVICE_STRATEGY_2()
        command_line = (
            self._MENU
            + ["--name", self._POOLNAME]
            + new_devices
            + ["--clevis=tang", "--thumbprint=print", "--tang-url=http"]
        )
        TEST_RUNNER(command_line)


class Migrate3TestCase(SimTestCase):
    """
    Test migrate with integrity options.
    """

    _MENU = ["--propagate", "pool", "migrate"]
    _DEVICES = _DEVICE_STRATEGY()
    _POOLNAME = "thispool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + self._DEVICES
        RUNNER(command_line)

    def test_invalid_journal_size(self):
        """
        Test migrating with an invalid journal size.
        """
        new_devices = _DEVICE_STRATEGY()
        command_line = (
            self._MENU
            + ["--name", self._POOLNAME]
            + new_devices
            + ["--journal-size=131079KiB"]
        )
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_too_large_journal_size(self):
        """
        Test migrating with a journal size that is too large for its D-Bus type.
        """
        new_devices = _DEVICE_STRATEGY()
        command_line = (
            self._MENU
            + ["--name", self._POOLNAME]
            + new_devices
            + ["--journal-size=18446744073709551616B"]
        )
        self.check_error(StratisCliUserError, command_line, _ERROR)


class Migrate4TestCase(SimTestCase):
    """
    Test migrate on non-existent pool.
    """

    _MENU = ["--propagate", "pool", "migrate"]
    _POOLNAME = "nonexistent"
    _DEVICES = _DEVICE_STRATEGY()

    def test_migrate_nonexistent(self):
        """
        Test that migrating a non-existent pool raises StratisCliResourceNotFoundError.
        """
        command_line = self._MENU + ["--name", self._POOLNAME] + self._DEVICES
        self.check_error(StratisCliResourceNotFoundError, command_line, _ERROR)
