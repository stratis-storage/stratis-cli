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
Test 'reset'.
"""

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import (
    StratisCliEngineError,
    StratisCliNoChangeError,
    StratisCliResourceNotFoundError,
)

from .._keyutils import RandomKeyTmpFile
from .._misc import RUNNER, SimTestCase

_ERROR = StratisCliErrorCodes.ERROR


class TestKeyReset(SimTestCase):
    """
    Test resetting a key in the keyring.
    """

    _MENU = ["--propagate", "key", "reset"]
    _KEYNAME = "testkey"

    def setUp(self):
        super().setUp()
        self._key_file = RandomKeyTmpFile()
        RUNNER(
            ["key", "set", self._KEYNAME, "--keyfile", self._key_file.tmpfile_name()]
        )

    def tearDown(self):
        super().tearDown()
        self._key_file.close()

    def test_reset(self):
        """
        Resetting to another random passphrase should succeed.
        """
        with RandomKeyTmpFile() as fname:
            command_line = self._MENU + [self._KEYNAME, "--keyfile-path", fname]
            RUNNER(command_line)

    def test_reset_no_change(self):
        """
        Resetting to the same passphrase should fail.
        """
        command_line = self._MENU + [
            self._KEYNAME,
            "--keyfile-path",
            self._key_file.tmpfile_name(),
        ]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)

    def test_reset_does_not_exist(self):
        """
        Resetting a key that does not exist should fail.
        """
        command_line = self._MENU + [
            "notakey",
            "--keyfile-path",
            self._key_file.tmpfile_name(),
        ]
        self.check_error(StratisCliResourceNotFoundError, command_line, _ERROR)

    def test_reset_key_too_long(self):
        """
        Resetting should fail due to the length of the key.
        """
        with RandomKeyTmpFile(128) as fname:
            command_line = self._MENU + [self._KEYNAME, "--keyfile-path", fname]
            self.check_error(StratisCliEngineError, command_line, _ERROR)
