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
Test 'explain'.
"""
# isort: LOCAL
from stratis_cli._constants import PoolMaintenanceErrorCode

from .._misc import TEST_RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(1)


class ExplainTestCase(SimTestCase):
    """
    Test 'explain'.
    """

    _MENU = ["--propagate", "pool", "explain"]

    def test_explain(self):
        """
        Test that every valid code works.
        """
        for item in list(PoolMaintenanceErrorCode):
            command_line = self._MENU + [str(item)]
            TEST_RUNNER(command_line)
