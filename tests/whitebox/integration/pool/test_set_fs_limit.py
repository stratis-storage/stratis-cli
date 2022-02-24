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
Test 'set-fs-limit'.
"""

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliEngineError, StratisCliPartialChangeError

from .._keyutils import RandomKeyTmpFile
from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(2)
_ERROR = StratisCliErrorCodes.ERROR


class SetFsLimitTestCase(SimTestCase):
    """
    Test 'set-fs-limit' with different values. 
    """

    _MENU = ["--propagate", "pool", "set-fs-limit"]
    _POOLNAME = "thispool"

    def setUp(self):
        """
        Start stratisd and set up a pool.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_set_fs_limit_neg(self):
        """
        Test setting the filesystem limit to a negative number.
        """
        command_line = self._MENU + [self._POOLNAME] + ["-1"] 
        self.check_error(StratisCliPartialChangeError, command_line, _ERROR)
