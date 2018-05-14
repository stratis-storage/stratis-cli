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
Test 'snapshot'.
"""

import unittest

from stratis_cli._errors import StratisCliActionError
from stratis_cli._errors import StratisCliDbusLookupError

from .._misc import _device_list
from .._misc import RUNNER
from .._misc import Service

_DEVICE_STRATEGY = _device_list(1)


class SnapshotTestCase(unittest.TestCase):
    """
    Test creating a snapshot of a filesystem in a pool.  In this case
    the snapshot should be created and no error raised.
    """
    _MENU = ['--propagate', 'filesystem', 'snapshot']
    _POOLNAME = 'deadpool'
    _SNAPNAME = 'snapfs'
    _FSNAME = 'fs'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = ['pool', 'create', self._POOLNAME] + \
                _DEVICE_STRATEGY.example()
        RUNNER(command_line)
        command_line = ['filesystem', 'create', self._POOLNAME, self._FSNAME]
        RUNNER(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testSnapshot(self):
        """
        Creation of the snapshot should succeed since origin pool/filesytem is available.
        """
        command_line = self._MENU + [
            self._POOLNAME, self._FSNAME, self._SNAPNAME
        ]
        RUNNER(command_line)


class Snapshot1TestCase(unittest.TestCase):
    """
    Test creating a snapshot w/out a pool.
    """
    _MENU = ['--propagate', 'filesystem', 'snapshot']
    _POOLNAME = 'nopool'
    _SNAPNAME = 'snapfs'
    _FSNAME = 'fs'

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

    def testCreation(self):
        """
        Creation of the snapshot must fail since specified pool does not exist.
        """
        command_line = self._MENU + [
            self._POOLNAME, self._FSNAME, self._SNAPNAME
        ]
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliDbusLookupError)


class Snapshot2TestCase(unittest.TestCase):
    """
    Test creating a snapshot w/out a filesystem.
    """
    _MENU = ['--propagate', 'filesystem', 'snapshot']
    _POOLNAME = 'pool'
    _FSNAME = 'fs'
    _SNAPNAME = 'snapfs'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = ['pool', 'create', self._POOLNAME] + \
                _DEVICE_STRATEGY.example()
        RUNNER(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testCreation(self):
        """
        Creation of the snapshot must fail since filesystem does not exist.
        """
        command_line = self._MENU + [
            self._POOLNAME, self._FSNAME, self._SNAPNAME
        ]
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliDbusLookupError)
