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
Test 'start'.
"""

# isort: STDLIB
from uuid import uuid4

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._constants import UnlockMethod
from stratis_cli._errors import (
    StratisCliEngineError,
    StratisCliInvalidCommandLineOptionValue,
    StratisCliNoChangeError,
    StratisCliResourceNotFoundError,
)

from .._misc import RUNNER, SimTestCase, device_name_list, stop_pool

_ERROR = StratisCliErrorCodes.ERROR
_DEVICE_STRATEGY = device_name_list(1, 1)


class StartTestCase(SimTestCase):
    """
    Test 'start' on a sim pool.
    """

    _MENU = ["--propagate", "pool", "start"]
    _POOLNAME = "poolname"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_bad_uuid(self):
        """
        Test trying to start a pool with non-existent UUID.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        command_line = self._MENU + [f"--uuid={uuid4()}"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_good_uuid(self):
        """
        Test trying to start a pool with a good UUID.
        """
        pool_uuid = stop_pool(self._POOLNAME)

        command_line = self._MENU + [f"--uuid={pool_uuid}"]
        RUNNER(command_line)

        self.check_error(StratisCliNoChangeError, command_line, _ERROR)

    def test_bad_name(self):
        """
        Test trying to start a pool with non-existent name.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        command_line = self._MENU + ["--name=bogus"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_good_name(self):
        """
        Test trying to start a pool with a good name.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        command_line = self._MENU + [f"--name={self._POOLNAME}"]
        RUNNER(command_line)

        self.check_error(StratisCliNoChangeError, command_line, _ERROR)

    def test_capture_key(self):
        """
        Test trying to start an unencrypted pool with a verified passphrase.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        command_line = self._MENU + [f"--name={self._POOLNAME}", "--capture-key"]
        self.check_error(
            StratisCliEngineError, command_line, _ERROR, stdin="password\n"
        )

    def test_unlock_method_any(self):
        """
        Test trying to start an unencrypted pool with unlock method ANY.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        command_line = self._MENU + [f"--name={self._POOLNAME}", "--unlock-method=any"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_token_slot_0(self):
        """
        Test trying to start an unencrypted pool with unlock method ANY.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        command_line = self._MENU + [f"--name={self._POOLNAME}", "--token-slot=0"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_method_clevis(self):
        """
        Test trying to start an unencrypted pool with unlock method clevis.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        command_line = self._MENU + [
            f"--name={self._POOLNAME}",
            f"--unlock-method={UnlockMethod.CLEVIS}",
        ]
        self.check_error(StratisCliInvalidCommandLineOptionValue, command_line, _ERROR)

    def test_method_keyring(self):
        """
        Test trying to start an unencrypted pool with unlock method keyring.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        command_line = self._MENU + [
            f"--name={self._POOLNAME}",
            f"--unlock-method={UnlockMethod.KEYRING}",
        ]
        self.check_error(StratisCliInvalidCommandLineOptionValue, command_line, _ERROR)

    def test_method_keyring_unknown_pool(self):
        """
        Test trying to start an unencrypted pool with unlock method keyring.
        """
        command_line = ["pool", "stop", f"--name={self._POOLNAME}"]
        RUNNER(command_line)
        command_line = self._MENU + [
            "--name=bogus",
            f"--unlock-method={UnlockMethod.KEYRING}",
        ]
        self.check_error(StratisCliResourceNotFoundError, command_line, _ERROR)

    def test_method_keyring_good_uuid(self):
        """
        Test trying to start an unencrypted pool with unlock method keyring, no
        token slot specified, and a UUID used to get the pool.
        """
        pool_uuid = stop_pool(self._POOLNAME)

        command_line = self._MENU + [f"--uuid={pool_uuid}", "--unlock-method=keyring"]
        self.check_error(StratisCliInvalidCommandLineOptionValue, command_line, _ERROR)
