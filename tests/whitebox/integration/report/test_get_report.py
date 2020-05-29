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
Test 'stratis report'.
"""

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliEngineError

from .._misc import SimTestCase, TEST_RUNNER

_ERROR = StratisCliErrorCodes.ERROR


class ReportTestCase(SimTestCase):
    """
    Test getting the errored pool and a nonexistent report"
    """

    _MENU = ["--propagate", "report"]

    def test_report(self):
        """
        Test getting errored pool report.
        """
        TEST_RUNNER(self._MENU + ["errored_pool_report"])

    def test_nonexistent_report(self):
        """
        Test getting nonexistent report.
        """
        self.check_error(StratisCliEngineError, self._MENU + ["notreport"], _ERROR)
