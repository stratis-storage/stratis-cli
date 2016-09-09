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
Test 'cache create'.
"""

import unittest

from stratis_cli._main import run
from stratis_cli._errors import StratisCliRuntimeError
from stratis_cli._stratisd_constants import StratisdErrorsGen

from ..._constants import _DEVICES

from ..._misc import _device_list
from ..._misc import Service


@unittest.skip('Cache created automatically when pool is created.')
class CreateTestCase(unittest.TestCase):
    """
    Test 'create' parsing.
    """
    _MENU = ['physical', 'cache', 'create']
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


@unittest.skip('Cache created automatically when pool is created.')
class Create2TestCase(unittest.TestCase):
    """
    Test 'create' with a non-existant pool.
    """
    _MENU = ['physical', 'cache', 'create']
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

    def testCreate(self):
        """
        Create should fail because the pool does not exist.
        """
        command_line = \
           self._MENU + \
           [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        with self.assertRaises(StratisCliRuntimeError) as ctxt:
            all(run(command_line))
        expected_error = StratisdErrorsGen.get_object().STRATIS_POOL_NOTFOUND
        self.assertEqual(ctxt.exception.rc, expected_error)


@unittest.skip('Cache created automatically when pool is created.')
@unittest.skip('unable to check status of devices')
class Create3TestCase(unittest.TestCase):
    """
    Test 'create' when pool exists.
    """
    _MENU = ['physical', 'cache', 'create']
    _POOLNAME = 'deadpool'
    _MY_DEVICES = [d.device_node for d in _device_list(_DEVICES, 2)]

    def _cache_devices(self):
        return self._MY_DEVICES[:1]

    def _pool_devices(self):
        return self._MY_DEVICES[1:]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = ['create', self._POOLNAME] + self._pool_devices()
        all(run(command_line))

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testCreate(self):
        """
        Create should succeed, assuming devices are not busy.
        """
        command_line = self._MENU + [self._POOLNAME] + self._cache_devices()
        all(run(command_line))


@unittest.skip('Cache created automatically when pool is created.')
class Create4TestCase(unittest.TestCase):
    """
    Test 'create' when pool exists and already has a cache.
    """
    _MENU = ['physical', 'cache', 'create']
    _POOLNAME = 'deadpool'
    _MY_DEVICES = [d.device_node for d in _device_list(_DEVICES, 2)]

    def _cache_devices(self):
        return self._MY_DEVICES[:1]

    def _other_devices(self):
        return self._MY_DEVICES[:1]

    def _pool_devices(self):
        return self._MY_DEVICES[1:]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = ['create', self._POOLNAME] + self._pool_devices()
        all(run(command_line))
        command_line = \
           ['physical', 'cache', 'create', self._POOLNAME] + \
           self._cache_devices()
        all(run(command_line))

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testCreate(self):
        """
        Create should fail, because there is already a cache.
        """
        command_line = self._MENU + [self._POOLNAME] + self._other_devices()
        with self.assertRaises(StratisCliRuntimeError) as ctxt:
            all(run(command_line))
        expected_error = StratisdErrorsGen.get_object().STRATIS_POOL_NOTFOUND
        self.assertEqual(ctxt.exception.rc, expected_error)
