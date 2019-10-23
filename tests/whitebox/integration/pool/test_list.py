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

from .._misc import RUNNER
from .._misc import SimTestCase
from .._misc import device_name_list

_DEVICE_STRATEGY = device_name_list(1)


class ListTestCase(SimTestCase):
    """
    Test 'list'.
    """

    _MENU = ["--propagate", "pool", "list"]

    def testList(self):
        """
        List should just succeed, even though there is nothing to list.
        """
        command_line = self._MENU
        RUNNER(command_line)

    def testListDefault(self):
        """
        Test default listing action when "list" is not specified.

        List should just succeed, even though there is nothing to list.
        """
        command_line = self._MENU[:-1]
        RUNNER(command_line)


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

    def testList(self):
        """
        List should just succeed.
        """
        command_line = self._MENU
        RUNNER(command_line)

    def testListDefault(self):
        """
        Test default listing action when "list" is not specified.
        """
        command_line = self._MENU[:-1]
        RUNNER(command_line)
