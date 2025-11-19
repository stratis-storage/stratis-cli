# Copyright 2021 Red Hat, Inc.
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
Test 'rebind'.
"""

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliEngineError, StratisCliNoChangeError

from .._keyutils import RandomKeyTmpFile
from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_ERROR = StratisCliErrorCodes.ERROR
_DEVICE_STRATEGY = device_name_list(1, 1)


class RebindTestCase(SimTestCase):
    """
    Test 'rebind' on a sim pool when the pool is unencrypted.
    """

    _MENU = ["--propagate", "pool", "rebind"]
    _POOLNAME = "poolname"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_rebind_with_clevis(self):
        """
        Rebinding with Clevis when unencrypted should return an error.
        """
        command_line = self._MENU + ["clevis", self._POOLNAME]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_rebind_with_key(self):
        """
        Rebinding with kernel keyring when unencrypted should return an error.
        """
        command_line = self._MENU + ["keyring", self._POOLNAME, "keydesc"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)


class RebindTestCase2(SimTestCase):
    """
    Rebind when pool is already encrypted using a key in the kernel keyring.
    """

    _MENU = ["--propagate", "pool", "rebind"]
    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        with RandomKeyTmpFile() as fname:
            command_line = [
                "--propagate",
                "key",
                "set",
                "--keyfile-path",
                fname,
                self._KEY_DESC,
            ]
            RUNNER(command_line)

        command_line = [
            "--propagate",
            "pool",
            "create",
            "--key-desc",
            self._KEY_DESC,
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_rebind_with_clevis(self):
        """
        Rebinding with Clevis when encrypted with key should return an error.
        """
        command_line = self._MENU + ["clevis", self._POOLNAME]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_rebind_keyring(self):
        """
        Rebinding with kernel keyring with same key should return an error.
        """
        command_line = self._MENU + ["keyring", self._POOLNAME, self._KEY_DESC]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)

    def test_rebind_keyring_new_key_description(self):
        """
        Rebinding with different kernel key description succeeds.
        """
        new_key_desc = "new_key_desc"
        with RandomKeyTmpFile() as fname:
            command_line = [
                "--propagate",
                "key",
                "set",
                "--keyfile-path",
                fname,
                new_key_desc,
            ]
            RUNNER(command_line)
        command_line = self._MENU + ["keyring", self._POOLNAME, new_key_desc]
        TEST_RUNNER(command_line)


class RebindTestCase3(SimTestCase):
    """
    Rebind when pool is already encrypted using tang.
    """

    _MENU = ["--propagate", "pool", "rebind"]
    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        command_line = [
            "--propagate",
            "pool",
            "create",
            self._POOLNAME,
            "--clevis=tang",
            "--trust-url",
            "--tang-url=http",
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_rebind_with_clevis(self):
        """
        Rebinding with Clevis should succeed.
        """
        command_line = self._MENU + ["clevis", self._POOLNAME]
        TEST_RUNNER(command_line)

    def test_rebind_keyring(self):
        """
        Rebinding with kernel keyring should return an error.
        """
        command_line = self._MENU + ["keyring", self._POOLNAME, self._KEY_DESC]
        self.check_error(StratisCliEngineError, command_line, _ERROR)
