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
Test 'bind'.
"""

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliEngineError, StratisCliNoChangeError

from .._keyutils import RandomKeyTmpFile
from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_ERROR = StratisCliErrorCodes.ERROR
_DEVICE_STRATEGY = device_name_list(1, 1)


class BindTestCase(SimTestCase):
    """
    Test 'bind' on a sim pool.
    """

    _MENU = ["--propagate", "pool", "bind"]
    _POOLNAME = "poolname"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_bind_when_unencrypted_tang(self):
        """
        Binding when unencrypted with tang should return an error.
        """
        command_line = self._MENU + [
            "nbde",
            self._POOLNAME,
            "URL",
            "--thumbprint",
            "fake thumbprint",
        ]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_bind_when_unencrypted_tang_trust(self):
        """
        Binding when unencrypted and trusting URL should return an error.
        """
        command_line = self._MENU + [
            "nbde",
            self._POOLNAME,
            "URL",
            "--trust-url",
        ]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_bind_when_unencrypted_tpm(self):
        """
        Binding when unencrypted with tpm should return an error.
        """
        command_line = self._MENU + [
            "tpm2",
            self._POOLNAME,
        ]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_bind_when_unencrypted_keyring(self):
        """
        Binding when unencrypted with keyring should return an error.
        """
        command_line = self._MENU + ["keyring", self._POOLNAME, "keydesc"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)


class BindTestCase2(SimTestCase):
    """
    Test binding when pool is encrypted.
    """

    _MENU = ["--propagate", "pool", "bind"]
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

    def test_bind_when_bound_1(self):
        """
        Binding when encrypted and bound should raise a no change error,
        as the action is assumed to be unintentional.
        """
        command_line = self._MENU + [
            "tpm2",
            self._POOLNAME,
        ]
        RUNNER(command_line)
        command_line = self._MENU + [
            "tpm2",
            self._POOLNAME,
        ]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)

    def test_bind_when_bound_2(self):
        """
        Binding when encrypted already should raise a no change error.
        """
        command_line = self._MENU + [
            "keyring",
            self._POOLNAME,
            self._KEY_DESC,
        ]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)


class BindTestCase3(SimTestCase):
    """
    Test binding when pool is encrypted.
    """

    _MENU = ["--propagate", "pool", "bind"]
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
            "--clevis=tpm2",
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_bind_when_bound(self):
        """
        Binding with keyring when already bound with clevis should succeed.
        """
        command_line = self._MENU + [
            "keyring",
            self._POOLNAME,
            self._KEY_DESC,
        ]
        TEST_RUNNER(command_line)
