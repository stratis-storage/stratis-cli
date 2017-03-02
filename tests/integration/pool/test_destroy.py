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
Test 'destroy'.
"""

import time
import unittest

from stratisd_client_dbus import StratisdErrorsGen

from stratis_cli._main import run
from stratis_cli._errors import StratisCliRuntimeError
from stratis_cli._errors import StratisCliDbusLookupError

from .._misc import _device_list
from .._misc import Service

_DEVICE_STRATEGY = _device_list(1)


class Destroy1TestCase(unittest.TestCase):
    """
    Test 'destroy' on empty database.

    'destroy' should always fail if pool is missing.
    """
    _MENU = ['pool', 'destroy']
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

    def testExecution(self):
        """
        Destroy should fail because there is no object path for the pool.
        """
        command_line = self._MENU + [self._POOLNAME]
        with self.assertRaises(StratisCliDbusLookupError):
            run(command_line)


class Destroy2TestCase(unittest.TestCase):
    """
    Test 'destroy' on database which contains the given pool.
    """
    _MENU = ['pool', 'destroy']
    _POOLNAME = 'deadpool'

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        time.sleep(1)
        command_line = \
           ['pool', 'create'] + \
           [self._POOLNAME] + \
           _DEVICE_STRATEGY.example()
        run(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testExecution(self):
        """
        The pool was just created, so must be destroyable.
        """
        command_line = self._MENU + [self._POOLNAME]
        run(command_line)


class Destroy3TestCase(unittest.TestCase):
    """
    Test 'destroy' on database which contains the given pool with a volume.
    """
    _MENU = ['pool', 'destroy']
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
           ['pool', 'create'] + \
           [self._POOLNAME] + \
           _DEVICE_STRATEGY.example()
        run(command_line)

        command_line = \
           ['filesystem', 'create'] + \
           [self._POOLNAME] + \
           [self._VOLNAME]
        run(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testExecution(self):
        """
        This should fail since it has a filesystem.
        """
        command_line = self._MENU + [self._POOLNAME]
        with self.assertRaises(StratisCliRuntimeError) as ctxt:
            run(command_line)
        expected_error = StratisdErrorsGen.get_object().BUSY
        self.assertEqual(ctxt.exception.rc, expected_error)

    def testWithFilesystemRemoved(self):
        """
        This should succeed since the filesystem is removed first.
        """
        command_line = ['filesystem', 'destroy', self._POOLNAME, self._VOLNAME]
        run(command_line)
        command_line = self._MENU + [self._POOLNAME]
        run(command_line)
