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
Test 'stratis debug'.
"""

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliSynthUeventError

from ._misc import TEST_RUNNER, SimTestCase

_ERROR = StratisCliErrorCodes.ERROR


class RefreshTestCase(SimTestCase):
    """
    Test the debug refresh command.
    """

    _MENU = ["--propagate", "debug"]

    def test_refresh(self):
        """
        Test calling refresh.
        """
        command_line = self._MENU + ["refresh"]
        TEST_RUNNER(command_line)


class UeventTestCase(SimTestCase):
    """
    Test the debug uevent command.
    """

    _MENU = ["--propagate", "debug"]

    def test_uevent(self):
        """
        Test calling uevent.
        """

        device = ["/dev/nonexistentdevice"]
        command_line = self._MENU + ["uevent"] + device
        self.check_error(StratisCliSynthUeventError, command_line, _ERROR)
