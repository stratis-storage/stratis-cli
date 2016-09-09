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

from stratis_cli._main import run
from stratis_cli._errors import StratisCliRuntimeError
from stratis_cli._stratisd_constants import StratisdErrorsGen

from .._constants import _DEVICES

from .._misc import _device_list
from .._misc import Service


class SnapshotTestCase(unittest.TestCase):
    """
    Test snapshot of a volume when pool does not exist.
    """
    _MENU = ['logical', 'snapshot']
    _POOLNAME = 'deadpool'
    _ORIGIN = 'here'
    _SNAP = 'there'

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

    def testSnapshot(self):
        """
        Snapshot of the volume must fail since there is no pool.
        """
        command_line = \
           self._MENU + [self._POOLNAME] + [self._ORIGIN] + [self._SNAP]
        with self.assertRaises(StratisCliRuntimeError) as ctxt:
            all(run(command_line))
        expected_error = StratisdErrorsGen.get_object().STRATIS_POOL_NOTFOUND
        self.assertEqual(ctxt.exception.rc, expected_error)


class Snapshot1TestCase(unittest.TestCase):
    """
    Test snapshot of a volume when pool exists but volume does not.
    """
    _MENU = ['logical', 'snapshot']
    _POOLNAME = 'deadpool'
    _ORIGIN = 'here'
    _SNAP = 'there'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = \
           ['create'] + [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))

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
        with self.assertRaises(StratisCliRuntimeError) as ctxt:
            all(run(command_line))
        expected_error = StratisdErrorsGen.get_object().STRATIS_VOLUME_NOTFOUND
        self.assertEqual(ctxt.exception.rc, expected_error)


@unittest.skip('not enough information to decide failure or success')
class Snapshot2TestCase(unittest.TestCase):
    """
    Test snapshot of a volume when pool and volume exists.
    """
    _MENU = ['logical', 'snapshot']
    _POOLNAME = 'deadpool'
    _ORIGIN = 'here'
    _SNAP = 'there'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = \
           ['create'] + [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))

        command_line = ['logical', 'create'] + [self._POOLNAME] + [self._ORIGIN]
        all(run(command_line))

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
        all(run(command_line))
