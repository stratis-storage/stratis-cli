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
Test 'overprovision'
"""

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes

from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(2)
_ERROR = StratisCliErrorCodes.ERROR


class SetOverprovisionModeTestCase(SimTestCase):
    """
    Test setting overprovision mode.
    """

    _MENU = ["--propagate", "pool", "overprovision"]
    _POOLNAME = "thispool"

    def setUp(self):
        """
        Start stratisd and set up a pool.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_set_overprovision_true(self):
        """
        Test setting overprovision mode to true.
        """
        command_line = self._MENU + [self._POOLNAME] + ["yes"]
        TEST_RUNNER(command_line)

    def test_set_overprovision_false(self):
        """
        Test setting overprovision mode to false.
        """
        command_line = self._MENU + [self._POOLNAME] + ["no"]
        TEST_RUNNER(command_line)
