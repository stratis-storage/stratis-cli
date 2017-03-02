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

from stratis_cli._main import run
from stratis_cli._errors import StratisCliDbusLookupError

from .._misc import _device_list
from .._misc import Service

_DEVICE_STRATEGY = _device_list(1)


class ListTestCase(unittest.TestCase):
    """
    Test listing a volume for a non-existant pool.
    """
    _MENU = ['filesystem', 'list']
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
        Listing the volume must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME]
        with self.assertRaises(StratisCliDbusLookupError):
            run(command_line)


class List2TestCase(unittest.TestCase):
    """
    Test listing volumes in an existing pool with no volumes.
    """
    _MENU = ['filesystem', 'list']
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
        run(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testList(self):
        """
        Listing the volumes in an empty pool should succeed.
        """
        command_line = self._MENU + [self._POOLNAME]
        run(command_line)


class List3TestCase(unittest.TestCase):
    """
    Test listing volumes in an existing pool with some volumes.
    """
    _MENU = ['filesystem', 'list']
    _POOLNAME = 'deadpool'
    _VOLUMES = ['livery', 'liberty', 'library']

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        time.sleep(1)
        command_line = \
           ['pool', 'create', self._POOLNAME] + \
           _DEVICE_STRATEGY.example()
        run(command_line)
        command_line = \
           ['filesystem', 'create', self._POOLNAME] + self._VOLUMES
        run(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testList(self):
        """
        Listing the volumes in a non-empty pool should succeed.
        """
        command_line = self._MENU + [self._POOLNAME]
        run(command_line)
