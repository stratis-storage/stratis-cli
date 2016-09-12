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

from stratis_cli._main import run
from stratis_cli._errors import StratisCliRuntimeError

from .._constants import _DEVICES

from .._misc import _device_list
from .._misc import Service


class CreateTestCase(unittest.TestCase):
    """
    Test 'create' parsing.
    """
    _MENU = ['pool', 'create']
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
        command_line = \
           self._MENU + \
           ['--redundancy', 'raid6'] + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        with self.assertRaises(SystemExit):
            all(run(command_line))


class Create2TestCase(unittest.TestCase):
    """
    Test 'create'.
    """
    _MENU = ['pool', 'create']
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

    @unittest.skip("not really handling this")
    def testCreate(self):
        """
        Create expects success unless devices are already occupied.
        """
        command_line = \
           self._MENU + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))


class Create3TestCase(unittest.TestCase):
    """
    Test 'create' on name collision.
    """
    _MENU = ['pool', 'create']
    _POOLNAME = 'deadpool'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = \
           ['pool', 'create', self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testCreate(self):
        """
        Create should fail trying to create new pool with same name as previous.
        """
        command_line = \
           self._MENU + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        with self.assertRaises(StratisCliRuntimeError):
            all(run(command_line))
