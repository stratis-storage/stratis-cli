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

from stratis_cli._errors import StratisCliRuntimeError

from .._misc import _device_list
from .._misc import RUNNER
from .._misc import Service

_DEVICE_STRATEGY = _device_list(1)


class CreateTestCase(unittest.TestCase):
    """
    Test 'create' parsing.
    """
    _MENU = ['--propagate', 'pool', 'create']
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

    def testRedundancy(self):
        """
        Parser error on all redundancy that is not 'none'.
        """
        command_line = self._MENU + ['--redundancy', 'raid6', self._POOLNAME] \
            + _DEVICE_STRATEGY.example()
        with self.assertRaises(SystemExit):
            RUNNER(command_line)


class Create3TestCase(unittest.TestCase):
    """
    Test 'create' on name collision.
    """
    _MENU = ['--propagate', 'pool', 'create']
    _POOLNAME = 'deadpool'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = ['pool', 'create', self._POOLNAME] \
            + _DEVICE_STRATEGY.example()
        RUNNER(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testCreate(self):
        """
        Create should fail trying to create new pool with same name as previous.
        """
        command_line = self._MENU + [self._POOLNAME] \
            + _DEVICE_STRATEGY.example()
        with self.assertRaises(StratisCliRuntimeError):
            RUNNER(command_line)
