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

from dbus_client_gen import DbusClientUniqueResultError

from stratis_cli._errors import StratisCliActionError

from .._misc import device_name_list
from .._misc import RUNNER
from .._misc import SimTestCase

_DEVICE_STRATEGY = device_name_list(1)


class ListTestCase(SimTestCase):
    """
    Test listing devices for a non-existant pool.
    """

    _MENU = ["--propagate", "blockdev", "list"]
    _POOLNAME = "deadpool"

    def testList(self):
        """
        Listing the devices must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME]
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, DbusClientUniqueResultError)

    def testListEmpty(self):
        """
        Listing the devices should succeed without a pool name specified.
        The list should be empty.
        """
        command_line = self._MENU
        RUNNER(command_line)

    def testListDefault(self):
        """
        Blockdev subcommand should default to listing all blockdevs for all
        pools. The list should be empty.
        """
        command_line = self._MENU[:-1]
        RUNNER(command_line)


class List2TestCase(SimTestCase):
    """
    Test listing devices in an existing pool.
    """

    _MENU = ["--propagate", "blockdev", "list"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create"] + [self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def testList(self):
        """
        Listing the devices should succeed.
        """
        command_line = self._MENU + [self._POOLNAME]
        RUNNER(command_line)

    def testListEmpty(self):
        """
        Listing the devices should succeed without a pool name specified.
        """
        command_line = self._MENU
        RUNNER(command_line)

    def testListDefault(self):
        """
        Blockdev subcommand should default to listing all blockdevs for all
        pools.
        """
        command_line = self._MENU[:-1]
        RUNNER(command_line)
