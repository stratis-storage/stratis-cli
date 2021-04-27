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
Test 'unbind'.
"""

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliEngineError, StratisCliNoChangeError

from .._keyutils import RandomKeyTmpFile
from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_ERROR = StratisCliErrorCodes.ERROR
_DEVICE_STRATEGY = device_name_list(1, 1)


class UnbindTestCase(SimTestCase):
    """
    Test 'unbind' on a sim pool.
    """

    _MENU = ["--propagate", "pool", "unbind"]
    _POOLNAME = "poolname"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_unbind_when_unencrypted(self):
        """
        Unbinding when unencrypted should return an error.
        """
        command_line = self._MENU + ["clevis", self._POOLNAME]
        self.check_error(StratisCliEngineError, command_line, _ERROR)


class UnbindTestCase2(SimTestCase):
    """
    Test unbinding when pool is encrypted.
    """

    _MENU = ["--propagate", "pool", "unbind"]
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

    def test_unbind_when_unbound(self):
        """
        Unbinding when encrypted but unbound should raise a no change error,
        as the action is assumed to be unintentional.
        """
        command_line = self._MENU + ["clevis", self._POOLNAME]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)

    def test_unbind_when_bound(self):
        """
        Bind and then unbind the pool. Unbinding should succeed.
        """
        command_line = [
            "--propagate",
            "pool",
            "bind",
            "nbde",
            self._POOLNAME,
            "URL",
            "--trust-url",
        ]
        RUNNER(command_line)
        command_line = self._MENU + ["clevis", self._POOLNAME]
        TEST_RUNNER(command_line)
