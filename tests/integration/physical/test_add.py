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

from stratis_cli._errors import StratisCliActionError
from stratis_cli._errors import StratisCliDbusLookupError

from .._misc import _device_list
from .._misc import RUNNER
from .._misc import Service

_DEVICE_STRATEGY = _device_list(1)


class AddDataTestCase(unittest.TestCase):
    """
    Test adding devices to a non-existant pool.
    """
    _MENU = ['--propagate', 'blockdev', 'add-data']
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

    def testAdd(self):
        """
        Adding the devices must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME] \
            + _DEVICE_STRATEGY.example()
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliDbusLookupError)


class AddCacheTestCase(unittest.TestCase):
    """
    Test adding devices to a non-existant pool.
    """
    _MENU = ['--propagate', 'blockdev', 'add-cache']
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

    def testAdd(self):
        """
        Adding the devices must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME] \
            + _DEVICE_STRATEGY.example()
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliDbusLookupError)
