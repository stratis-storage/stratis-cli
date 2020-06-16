# Copyright 2016 Red Hat, Inc.
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

from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(1)


class ListTestCase(SimTestCase):
    """
    Test 'list'.
    """

    _MENU = ["--propagate", "pool", "list"]

    def test_list(self):
        """
        List should just succeed, even though there is nothing to list.
        """
        command_line = self._MENU
        TEST_RUNNER(command_line)

    def test_list_default(self):
        """
        Test default listing action when "list" is not specified.

        List should just succeed, even though there is nothing to list.
        """
        command_line = self._MENU[:-1]
        TEST_RUNNER(command_line)


class List2TestCase(SimTestCase):
    """
    Test 'list' with something actually to list.
    """

    _MENU = ["--propagate", "pool", "list"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_list(self):
        """
        List should just succeed.
        """
        command_line = self._MENU
        TEST_RUNNER(command_line)

    def test_list_default(self):
        """
        Test default listing action when "list" is not specified.
        """
        command_line = self._MENU[:-1]
        TEST_RUNNER(command_line)

    def test_list_with_cache(self):
        """
        Test listing a pool with a cache. The purpose is to verify that
        strings representing boolean values with a True value are handled.
        """
        command_line = ["pool", "init-cache", self._POOLNAME] + _DEVICE_STRATEGY()
        TEST_RUNNER(command_line)
        command_line = self._MENU
        TEST_RUNNER(command_line)
