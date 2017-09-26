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

import time
import unittest

from stratis_cli._errors import StratisCliRuntimeError

from .._misc import _device_list
from .._misc import RUNNER
from .._misc import Service


_DEVICE_STRATEGY = _device_list(1)


@unittest.skip("unimplemented")
class SnapshotTestCase(unittest.TestCase):
    """
    Test snapshot of a volume when pool does not exist.
    """
    _MENU = ['--propagate', 'filesystem', 'snapshot']
    _POOLNAME = 'deadpool'
    _ORIGIN = 'here'
    _SNAP = 'there'

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

    def testSnapshot(self):
        """
        Snapshot of the volume must fail since there is no pool.
        """
        command_line = \
           self._MENU + [self._POOLNAME] + [self._ORIGIN] + [self._SNAP]
        with self.assertRaises(StratisCliRuntimeError):
            RUNNER(command_line)
        # currently no error defined
        # self.assertEqual(ctxt.exception.rc, StratisdErrors.POOL_NOTFOUND)


@unittest.skip("unimplemented")
class Snapshot1TestCase(unittest.TestCase):
    """
    Test snapshot of a volume when pool exists but volume does not.
    """
    _MENU = ['--propagate', 'filesystem', 'snapshot']
    _POOLNAME = 'deadpool'
    _ORIGIN = 'here'
    _SNAP = 'there'

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

    def testSnapshot(self):
        """
        Snapshot of the volume must fail since there is no volume.
        """
        command_line = \
           self._MENU + [self._POOLNAME] + [self._ORIGIN] + [self._SNAP]
        with self.assertRaises(StratisCliRuntimeError):
            RUNNER(command_line)
        # Returned error currently undefined.
        # self.assertEqual(ctxt.exception.rc, StratisdErrors.VOLUME_NOTFOUND)


@unittest.skip('unimplemented')
class Snapshot2TestCase(unittest.TestCase):
    """
    Test snapshot of a volume when pool and volume exists.
    """
    _MENU = ['--propagate', 'filesystem', 'snapshot']
    _POOLNAME = 'deadpool'
    _ORIGIN = 'here'
    _SNAP = 'there'

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

        command_line = ['filesystem', 'create'] + [self._POOLNAME] + [self._ORIGIN]
        RUNNER(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testSnapshot(self):
        """
        Snapshot of the volume could fail if not enough space in pool, should
        succeed if enough space in pool.
        """
        command_line = \
           self._MENU + [self._POOLNAME] + [self._ORIGIN] + [self._SNAP]
        RUNNER(command_line)
