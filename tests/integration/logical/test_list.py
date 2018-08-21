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
from stratis_cli._errors import StratisCliUniqueLookupError

from .._misc import _device_list
from .._misc import RUNNER
from .._misc import Service

_DEVICE_STRATEGY = _device_list(1)


class ListTestCase(unittest.TestCase):
    """
    Test listing a volume for a non-existant pool.
    """
    _MENU = ['--propagate', 'filesystem', 'list']
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
        Listing the volume must fail since the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME]
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliUniqueLookupError)


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
        command_line = ['pool', 'create'] + [self._POOLNAME] \
            +  _DEVICE_STRATEGY.example()
        RUNNER(command_line)

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
        RUNNER(command_line)


@unittest.skip(
    "Temporarily unable to create multiple filesystems at same time")
class List3TestCase(unittest.TestCase):
    """
    Test listing volumes in an existing pool with some volumes.
    """
    _MENU = ['--propagate', 'filesystem', 'list']
    _POOLNAME = 'deadpool'
    _VOLUMES = ['livery', 'liberty', 'library']

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = ['pool', 'create', self._POOLNAME] \
            + _DEVICE_STRATEGY.example()
        RUNNER(command_line)
        command_line = ['filesystem', 'create', self._POOLNAME] + self._VOLUMES
        RUNNER(command_line)

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
        RUNNER(command_line)


class List4TestCase(unittest.TestCase):
    """
    Test listing volumes in an existing pool with some volumes.
    """
    _POOLNAME = 'deadpool'
    _VOLUMES = ['livery', 'liberty', 'library']

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = ['pool', 'create', self._POOLNAME] \
            + _DEVICE_STRATEGY.example()
        RUNNER(command_line)

        command_line = [
            'filesystem', 'create', self._POOLNAME, self._VOLUMES[0]
        ]
        RUNNER(command_line)
        command_line = [
            'filesystem', 'create', self._POOLNAME, self._VOLUMES[1]
        ]
        RUNNER(command_line)
        command_line = [
            'filesystem', 'create', self._POOLNAME, self._VOLUMES[2]
        ]
        RUNNER(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testList(self):
        """
        Listing multiple volumes in a non-empty pool should succeed.
        """
        command_line = ['--propagate', 'filesystem', 'list', self._POOLNAME]
        RUNNER(command_line)

        # Also should work when no pool name is given
        command_line = ['--propagate', 'filesystem']
        RUNNER(command_line)

        # Also should work using 'fs' alias
        command_line = ['--propagate', 'fs']
        RUNNER(command_line)
