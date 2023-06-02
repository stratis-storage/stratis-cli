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
Test 'set'.
"""

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import (
    StratisCliEngineError,
    StratisCliKeyfileNotFoundError,
    StratisCliNameConflictError,
)

from .._keyutils import RandomKeyTmpFile
from .._misc import RUNNER, TEST_RUNNER, SimTestCase

_ERROR = StratisCliErrorCodes.ERROR


class TestKeySet(SimTestCase):
    """
    Test setting a key in the keyring.
    """

    _MENU = ["--propagate", "key", "set"]
    _KEYNAME = "testkey"

    def test_set(self):
        """
        Setting should succeed.
        """
        with RandomKeyTmpFile() as fname:
            command_line = self._MENU + [self._KEYNAME, "--keyfile-path", fname]
            TEST_RUNNER(command_line)

    def test_set_conflict(self):
        """
        Setting should fail due to name conflict.
        """
        with RandomKeyTmpFile() as fname:
            command_line = self._MENU + [self._KEYNAME, "--keyfile-path", fname]
            RUNNER(command_line)
            self.check_error(StratisCliNameConflictError, command_line, _ERROR)

    def test_set_key_too_long(self):
        """
        Setting should fail due to the length of the key.
        """
        with RandomKeyTmpFile(128) as fname:
            command_line = self._MENU + [self._KEYNAME, "--keyfile-path", fname]
            self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_set_key_filename_missing(self):
        """
        Test that specifying a filename that does not exist raises a
        StratisCliKeyfileNotFoundError.
        """
        command_line = self._MENU + [self._KEYNAME, "--keyfile-path", "/bogus"]
        self.check_error(StratisCliKeyfileNotFoundError, command_line, _ERROR)

    def test_set_key_capture_key_fail_verify(self):
        """
        Test capture key fails if passphrase do not match
        """
        command_line = self._MENU + [self._KEYNAME, "--capture-key"]
        with patch.object(_top, "getpass", side_effect=["totally_secret", "different"]):
            self.check_error(StratisCliPassphraseMismatchError, command_line, _ERROR)
