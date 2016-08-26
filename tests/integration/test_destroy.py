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

from ._constants import _DEVICES

from ._misc import _device_list
from ._misc import Service


class Destroy1TestCase(unittest.TestCase):
    """
    Test 'destroy' on empty database.

    'destroy' should always succeed on an empty database.
    """
    _MENU = ['destroy']
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

    def testWithoutForce(self):
        """
        Destroy should succeed w/out --force.
        """
        command_line = self._MENU + [self._POOLNAME]
        all(run(command_line))

    def testWithForce(self):
        """
        If pool does not exist and --force is set, command should succeed.
        """
        command_line = self._MENU + ['--force', '2'] + [self._POOLNAME]
        all(run(command_line))


class Destroy2TestCase(unittest.TestCase):
    """
    Test 'destroy' on database which contains the given pool.
    """
    _MENU = ['destroy']
    _POOLNAME = 'deadpool'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = \
           ['create'] + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testWithoutForce(self):
        """
        The pool was just created, so must be destroyable w/out force.
        """
        command_line = self._MENU + [self._POOLNAME]
        all(run(command_line))

    def testWithForce(self):
        """
        Since it should succeed w/out force, it should succeed w/ force.
        """
        command_line = self._MENU + ['--force', '1'] + [self._POOLNAME]
        all(run(command_line))


class Destroy3TestCase(unittest.TestCase):
    """
    Test 'destroy' on database which contains the given pool and a volume.

    Verify that the volume is gone when the pool is gone.
    """
    _MENU = ['destroy']
    _POOLNAME = 'deadpool'
    _VOLNAME = 'vol'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()

        command_line = \
           ['create'] + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))

        command_line = \
           ['logical', 'create'] + \
           [self._POOLNAME] + \
           [self._VOLNAME]
        all(run(command_line))

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    @unittest.expectedFailure
    def testWithoutForce(self):
        """
        This should fail with a force value of 0, since it has a volume.
        """
        command_line = self._MENU + [self._POOLNAME]
        with self.assertRaises(StratisCliRuntimeError):
            all(run(command_line))

    def testWithForce1(self):
        """
        Should succeed w/ force value of 1, since it has volumes but no data.
        """
        command_line = self._MENU + ['--force', '1'] + [self._POOLNAME]
        all(run(command_line))

    def testWithForce2(self):
        """
        Should succeed w/ force value of 2, since it has volumes but no data.
        """
        command_line = self._MENU + ['--force', '2'] + [self._POOLNAME]
        all(run(command_line))
