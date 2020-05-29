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
Test 'list'.
"""

from .._keyutils import RandomKeyTmpFile
from .._misc import RUNNER, TEST_RUNNER, SimTestCase


class TestKeyList(SimTestCase):
    """
    Test listing the keys in the keyring.
    """

    _MENU = ["key", "list"]

    def test_list(self):
        """
        Listing should succeed.
        """
        TEST_RUNNER(self._MENU)

    def test_list_one(self):
        """
        Listing should succeed.
        """
        with RandomKeyTmpFile() as fname:
            RUNNER(["key", "set", "testkey", "--keyfile", fname])
        TEST_RUNNER(self._MENU)
