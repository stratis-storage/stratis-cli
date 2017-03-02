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

from stratisd_client_dbus import get_object

from stratis_cli import run

from stratis_cli._actions._misc import GetObjectPath

from stratis_cli._constants import TOP_OBJECT
from stratis_cli._errors import StratisCliDbusLookupError

from ._misc import _device_list
from ._misc import Service


_DEVICE_STRATEGY = _device_list(1)

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
        time.sleep(1)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testNonExistingPool(self):
        """
        An exception is raised if the pool does not exist.
        """
        with self.assertRaises(StratisCliDbusLookupError):
            GetObjectPath.get_pool(get_object(TOP_OBJECT), {'Name': 'notapool'})


class GetPool1TestCase(unittest.TestCase):
    """
    Test get_pool method when there is a pool.
    """
    _POOLNAME = 'deadpool'

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

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testExistingPool(self):
        """
        The pool should be gotten.
        """
        self.assertIsNotNone(
           GetObjectPath.get_pool(
              get_object(TOP_OBJECT),
              spec={'Name': self._POOLNAME}
           )
        )

    def testNonExistingPool(self):
        """
        An exception is raised if the pool does not exist.
        """
        with self.assertRaises(StratisCliDbusLookupError):
            GetObjectPath.get_pool(get_object(TOP_OBJECT), {'Name': 'notapool'})


class GetVolume1TestCase(unittest.TestCase):
    """
    Test get_filesystem method when there is a pool but no volume.
    """
    _POOLNAME = 'deadpool'

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

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testNonExistingVolume(self):
        """
        An exception is raised if the volume does not exist.
        """
        proxy = get_object(TOP_OBJECT)
        pool_object_path = \
           GetObjectPath.get_pool(proxy, spec={'Name': self._POOLNAME})

        with self.assertRaises(StratisCliDbusLookupError):
            GetObjectPath.get_filesystem(
               proxy,
               {'Name': 'noname', 'Pool': pool_object_path}
            )


class GetVolume2TestCase(unittest.TestCase):
    """
    Test get_filesystem method when there is a pool and the volume is there.
    """
    _POOLNAME = 'deadpool'
    _VOLNAME = 'vol'

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
           ['filesystem', 'create', self._POOLNAME, self._VOLNAME]
        run(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testExistingVolume(self):
        """
        The volume should be discovered.
        """
        proxy = get_object(TOP_OBJECT)
        pool_object_path = \
           GetObjectPath.get_pool(proxy, spec={'Name': self._POOLNAME})

        self.assertIsNotNone(
            GetObjectPath.get_filesystem(
               proxy,
               {'Name': self._VOLNAME, 'Pool': pool_object_path}
            )
        )

    def testNonExistingVolume(self):
        """
        An exception is raised if the volume does not exist.
        """
        proxy = get_object(TOP_OBJECT)
        pool_object_path = \
           GetObjectPath.get_pool(proxy, spec={'Name': self._POOLNAME})

        with self.assertRaises(StratisCliDbusLookupError):
            GetObjectPath.get_filesystem(
               proxy,
               {'Name': 'noname', 'Pool': pool_object_path}
            )
