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
Test 'unlock'.
"""

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliNoChangeError

from .._misc import SimTestCase

_ERROR = StratisCliErrorCodes.ERROR


class UnlockTestCase(SimTestCase):
    """
    Test 'unlock' when no pools are locked (the only state in the sim_engine).
    """

    _MENU = ["--propagate", "pool", "unlock"]

    def test_unlock(self):
        """
        This should fail because no pools can be unlocked.
        """
        self.check_error(StratisCliNoChangeError, self._MENU, _ERROR)
