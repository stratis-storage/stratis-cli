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
Test 'unset'.
"""

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliNoChangeError

from .._keyutils import RandomKeyTmpFile
from .._misc import RUNNER, SimTestCase

_ERROR = StratisCliErrorCodes.ERROR


class TestKeyUnset(SimTestCase):
    """
    Test unsetting a key in the keyring.
    """

    _MENU = ["--propagate", "key", "unset"]
    _KEYNAME = "testkey"

    def setUp(self):
        super().setUp()
        self._key_file = RandomKeyTmpFile()
        RUNNER(
            ["key", "set", self._KEYNAME, "--keyfile", self._key_file.tmpfile_name()]
        )

    def test_unset(self):
        """
        Unsetting should succeed.
        """
        command_line = self._MENU + [self._KEYNAME]
        RUNNER(command_line)

    def test_unset_does_not_exist(self):
        """
        Unsetting should fail due to key not existing.
        """
        command_line = self._MENU + ["doesnotexist"]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)
