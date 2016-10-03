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
Test destroying a filesystem in a pool.
"""

import time
import unittest

from stratis_cli._actions._stratisd_constants import StratisdErrorsGen

from stratis_cli._constants import TOP_OBJECT

from stratis_cli._dbus import Manager
from stratis_cli._dbus import Pool
from stratis_cli._dbus import get_object

from .._constants import _DEVICES

from .._misc import _device_list
from .._misc import Service


class DestroyFSTestCase(unittest.TestCase):
    """
    Test with an empty pool.
    """

    _POOLNAME = 'deadpool'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        time.sleep(1)
        self._proxy = get_object(TOP_OBJECT)
        self._devs = [d.device_node for d in _device_list(_DEVICES, 1)]
        (result, _, _) = Manager(self._proxy).CreatePool(
           self._POOLNAME,
           self._devs,
           0
        )
        self._pool_object = get_object(result)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testDestroyNone(self):
        """
        Test calling with no actual volume specification. An empty volume
        list should always succeed, and it should not decrease the
        number of volumes.
        """
        (result, rc, message) = Pool(self._pool_object).DestroyVolumes([])
        self.assertIsInstance(result, list)
        self.assertIsInstance(rc, int)
        self.assertIsInstance(message, str)

        self.assertEqual(len(result), 0)
        self.assertEqual(rc, StratisdErrorsGen.get_object().STRATIS_OK)

        (result, rc, message) = Pool(self._pool_object).ListVolumes()
        self.assertEqual(rc, StratisdErrorsGen.get_object().STRATIS_OK)
        self.assertEqual(len(result), 0)

    def testDestroyOne(self):
        """
        Test calling with a non-existant volume name. This should succeed,
        because at the end the volume is not there.
        """

        (result, rc, message) = Pool(self._pool_object).DestroyVolumes(['name'])
        self.assertIsInstance(result, list)
        self.assertIsInstance(rc, int)
        self.assertIsInstance(message, str)

        self.assertEqual(len(result), 0)
        self.assertEqual(rc, StratisdErrorsGen.get_object().STRATIS_OK)

        (result, rc, message) = Pool(self._pool_object).ListVolumes()
        self.assertEqual(rc, StratisdErrorsGen.get_object().STRATIS_OK)
        self.assertEqual(len(result), 0)


class DestroyFSTestCase1(unittest.TestCase):
    """
    Make a filesystem for the pool.
    """

    _POOLNAME = 'deadpool'
    _VOLNAME = 'thunk'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        time.sleep(1)
        self._proxy = get_object(TOP_OBJECT)
        self._devs = [d.device_node for d in _device_list(_DEVICES, 1)]
        (result, _, _) = Manager(self._proxy).CreatePool(
           self._POOLNAME,
           self._devs,
           0
        )
        self._pool_object = get_object(result)
        Pool(self._pool_object).CreateVolumes([(self._VOLNAME, '', '')])

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testDestroy(self):
        """
        Test calling by specifying the volume name. Assume that destruction
        should always succeed.
        """
        (result, rc, message) = \
           Pool(self._pool_object).DestroyVolumes([self._VOLNAME])
        self.assertIsInstance(result, list)
        self.assertIsInstance(rc, int)
        self.assertIsInstance(message, str)

        self.assertEqual(rc, StratisdErrorsGen.get_object().STRATIS_OK)
        self.assertEqual(len(result), 1)

        (result, rc, message) = result[0]
        self.assertIsInstance(result, str)
        self.assertIsInstance(rc, int)
        self.assertIsInstance(message, str)

        self.assertEqual(rc, StratisdErrorsGen.get_object().STRATIS_OK)

        (result, rc, message) = Pool(self._pool_object).ListVolumes()
        self.assertEqual(rc, StratisdErrorsGen.get_object().STRATIS_OK)
        self.assertEqual(len(result), 0)
