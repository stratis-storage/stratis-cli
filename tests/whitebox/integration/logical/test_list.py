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
Test 'create'.
"""

import unittest

from dbus_client_gen import DbusClientUniqueResultError

from stratis_cli._errors import StratisCliActionError

from .._misc import device_name_list
from .._misc import RUNNER
from .._misc import SimTestCase

_DEVICE_STRATEGY = device_name_list(1)


class ListTestCase(SimTestCase):
    """
    Test listing a volume for a non-existant pool.
    """

    _MENU = ["--propagate", "filesystem", "list"]
    _POOLNAME = "deadpool"

    def testList(self):
        """
        Listing the volume must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME]
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, DbusClientUniqueResultError)


class List2TestCase(SimTestCase):
    """
    Test listing volumes in an existing pool with no volumes.
    """

    _MENU = ["--propagate", "filesystem", "list"]
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
        Listing the volumes in an empty pool should succeed.
        """
        command_line = self._MENU + [self._POOLNAME]
        RUNNER(command_line)


@unittest.skip("Temporarily unable to create multiple filesystems at same time")
class List3TestCase(SimTestCase):
    """
    Test listing volumes in an existing pool with some volumes.
    """

    _MENU = ["--propagate", "filesystem", "list"]
    _POOLNAME = "deadpool"
    _VOLUMES = ["livery", "liberty", "library"]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)
        command_line = ["filesystem", "create", self._POOLNAME] + self._VOLUMES
        RUNNER(command_line)

    def testList(self):
        """
        Listing the volumes in a non-empty pool should succeed.
        """
        command_line = self._MENU + [self._POOLNAME]
        RUNNER(command_line)


class List4TestCase(SimTestCase):
    """
    Test listing volumes in an existing pool with some volumes.
    """

    _POOLNAME = "deadpool"
    _VOLUMES = ["livery", "liberty", "library"]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        command_line = ["filesystem", "create", self._POOLNAME, self._VOLUMES[0]]
        RUNNER(command_line)
        command_line = ["filesystem", "create", self._POOLNAME, self._VOLUMES[1]]
        RUNNER(command_line)
        command_line = ["filesystem", "create", self._POOLNAME, self._VOLUMES[2]]
        RUNNER(command_line)

    def testList(self):
        """
        Listing multiple volumes in a non-empty pool should succeed.
        """
        command_line = ["--propagate", "filesystem", "list", self._POOLNAME]
        RUNNER(command_line)


class List5TestCase(SimTestCase):
    """
    Test correctness of alternative list options.
    """

    _POOLNAMES = ["deadpool", "otherpool", "emptypool"]
    _VOLUMES = ["livery", "liberty", "library"]
    _MENU = ["--propagate", "filesystem", "list"]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAMES[0]] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        command_line = ["filesystem", "create", self._POOLNAMES[0], self._VOLUMES[0]]
        RUNNER(command_line)
        command_line = ["filesystem", "create", self._POOLNAMES[0], self._VOLUMES[1]]
        RUNNER(command_line)
        command_line = ["pool", "create", self._POOLNAMES[1]] + _DEVICE_STRATEGY()
        RUNNER(command_line)
        command_line = ["filesystem", "create", self._POOLNAMES[1], self._VOLUMES[2]]
        RUNNER(command_line)
        command_line = ["pool", "create", self._POOLNAMES[2]] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def testListOne(self):
        """
        Specifying a pool name should yield only filesystems for that pool.
        """
        command_line = self._MENU + [self._POOLNAMES[1]]
        RUNNER(command_line)

    def testListNoPool(self):
        """
        If pool name is not specified, all filesystems for all pools should
        be listed.
        """
        command_line = self._MENU
        RUNNER(command_line)

    def testListDefault(self):
        """
        filesystem or fs subcommand should default to listing all pools.
        """
        command_line = self._MENU[:-1]
        RUNNER(command_line)

        command_line = ["--propagate", "fs"]
        RUNNER(command_line)
