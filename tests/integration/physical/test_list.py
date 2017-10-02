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

import time
import unittest

from stratis_cli._errors import StratisCliDbusLookupError

from .._misc import _device_list
from .._misc import RUNNER
from .._misc import Service

_DEVICE_STRATEGY = _device_list(1)


@unittest.skip("Not currently listing devices in DBus API.")
class ListTestCase(unittest.TestCase):
    """
    Test listing devices for a non-existant pool.
    """
    _MENU = ['--propagate', 'blockdev', 'list']
    _POOLNAME = 'deadpool'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        time.sleep(1)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testList(self):
        """
        Listing the devices must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME]
        with self.assertRaises(StratisCliDbusLookupError):
            RUNNER(command_line)


@unittest.skip("Not currently listing devices in DBus API.")
class List2TestCase(unittest.TestCase):
    """
    Test listing devices in an existing pool.
    """
    _MENU = ['--propagate', 'blockdev', 'list']
    _POOLNAME = 'deadpool'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        time.sleep(1)
        command_line = \
           ['pool', 'create'] + [self._POOLNAME] + \
           _DEVICE_STRATEGY.example()
        RUNNER(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testList(self):
        """
        Listing the devices should succeed.
        """
        command_line = self._MENU + [self._POOLNAME]
        RUNNER(command_line)
