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
Test miscellaneous methods.
"""
import time
import unittest

from stratis_cli import run

from stratis_cli._actions._misc import get_cache
from stratis_cli._actions._misc import get_pool
from stratis_cli._actions._misc import get_volume

from stratis_cli._constants import TOP_OBJECT
from stratis_cli._dbus import get_object
from stratis_cli._errors import StratisCliRuntimeError
from stratis_cli._stratisd_constants import StratisdErrorsGen

from ._constants import _DEVICES

from ._misc import _device_list
from ._misc import Service


class GetObjectTestCase(unittest.TestCase):
    """
    Test get_object method.
    """

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

    def testNonExisting(self):
        """
        A proxy object is returned from a non-existant path.
        """
        time.sleep(1) # wait until the service is available
        self.assertIsNotNone(get_object('/this/is/not/an/object/path'))

    def testInvalid(self):
        """
        An invalid path causes an exception to be raised.
        """
        with self.assertRaises(ValueError):
            get_object('abc')


class GetPoolTestCase(unittest.TestCase):
    """
    Test get_pool method when there is no pool.

    It should raise an exception.
    """

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

    def testNonExistingPool(self):
        """
        An exception is raised if the pool does not exist.
        """
        time.sleep(1) # wait until the service is available
        with self.assertRaises(StratisCliRuntimeError) as ctxt:
            get_pool(get_object(TOP_OBJECT), 'notapool')
        expected_error = StratisdErrorsGen.get_object().STRATIS_POOL_NOTFOUND
        self.assertEqual(ctxt.exception.rc, expected_error)


class GetPool1TestCase(unittest.TestCase):
    """
    Test get_pool method when there is a pool.
    It should succeed.
    """
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

    def testNonExistingVolume(self):
        """
        An exception is raised if the volume does not exist.
        """
        time.sleep(1) # wait until the service is available
        self.assertIsNotNone(get_pool(get_object(TOP_OBJECT), self._POOLNAME))


class GetVolumeTestCase(unittest.TestCase):
    """
    Test get_volume method when there is no pool.

    It should raise an exception.
    """

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

    def testNonExistingPool(self):
        """
        An exception is raised if the pool does not exist.
        """
        time.sleep(1) # wait until the service is available
        with self.assertRaises(StratisCliRuntimeError) as ctxt:
            get_volume(get_object(TOP_OBJECT), 'notapool', 'noname')
        expected_error = StratisdErrorsGen.get_object().STRATIS_POOL_NOTFOUND
        self.assertEqual(ctxt.exception.rc, expected_error)


class GetVolume1TestCase(unittest.TestCase):
    """
    Test get_volume method when there is a pool but no volume.
    It should raise an exception.
    """
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

    def testNonExistingVolume(self):
        """
        An exception is raised if the volume does not exist.
        """
        time.sleep(1) # wait until the service is available
        with self.assertRaises(StratisCliRuntimeError) as ctxt:
            get_volume(get_object(TOP_OBJECT), self._POOLNAME, 'noname')
        expected_error = StratisdErrorsGen.get_object().STRATIS_VOLUME_NOTFOUND
        self.assertEqual(ctxt.exception.rc, expected_error)


class GetVolume2TestCase(unittest.TestCase):
    """
    Test get_volume method when there is a pool and the volume is there.
    It should succeed.
    """
    _POOLNAME = 'deadpool'
    _VOLNAME = 'vol'

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
        command_line = \
           ['filesystem', 'create', self._POOLNAME, self._VOLNAME]
        all(run(command_line))

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testExistingVolume(self):
        """
        The volume should be discovered.
        """
        time.sleep(1) # wait until the service is available
        get_volume(get_object(TOP_OBJECT), self._POOLNAME, self._VOLNAME)


class GetCacheTestCase(unittest.TestCase):
    """
    Test get_cache method when there is no pool.

    It should raise an exception.
    """

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

    @unittest.expectedFailure
    def testNonExistingPool(self):
        """
        An exception is raised if the pool does not exist.
        """
        time.sleep(1) # wait until the service is available
        with self.assertRaises(StratisCliRuntimeError) as ctxt:
            get_cache(get_object(TOP_OBJECT), 'notapool')
        expected_error = StratisdErrorsGen.get_object().STRATIS_POOL_NOTFOUND
        self.assertEqual(ctxt.exception.rc, expected_error)


class GetCache1TestCase(unittest.TestCase):
    """
    Test get_cache method when there is a pool.
    It should succeed because the pool is created automatically.
    """
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

    @unittest.expectedFailure
    def testExecution(self):
        """
        An exception is raised if the volume does not exist.
        """
        time.sleep(1) # wait until the service is available
        self.assertIsNotNone(get_cache(get_object(TOP_OBJECT), self._POOLNAME))
