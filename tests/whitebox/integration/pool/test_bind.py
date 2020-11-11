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
from stratis_cli._errors import StratisCliEngineError

from .._misc import RUNNER, SimTestCase, device_name_list

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
            "fake_key",
            "URL",
            "--thumbprint",
            "fake thumbprint",
        ]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_bind_when_unencrypted_tpm(self):
        """
        Binding when unencrypted with tpm should return an error.
        """
        command_line = self._MENU + [
            "tpm",
            self._POOLNAME,
            "fake_key",
        ]
        self.check_error(StratisCliEngineError, command_line, _ERROR)
