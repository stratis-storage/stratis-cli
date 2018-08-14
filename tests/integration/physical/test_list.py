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

import unittest

from stratis_cli._errors import StratisCliActionError
from stratis_cli._errors import StratisCliUniqueLookupError

from .._misc import _device_list
from .._misc import RUNNER
from .._misc import Service

_DEVICE_STRATEGY = _device_list(1)


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
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliUniqueLookupError)

    def testListEmpty(self):
        """
        Listing the devices should succeed without a pool name specified.
        The list should be empty.
        """
        command_line = self._MENU
        RUNNER(command_line)


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
        command_line = ['pool', 'create'] + [self._POOLNAME] \
            + _DEVICE_STRATEGY.example()
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

    def testListEmpty(self):
        """
        Listing the devices should succeed without a pool name specified.
        """
        command_line = self._MENU
        RUNNER(command_line)
