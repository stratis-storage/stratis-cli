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

import time
import unittest


from stratis_cli._errors import StratisCliRuntimeError
from stratis_cli._errors import StratisCliDbusLookupError

from stratis_cli._stratisd_constants import StratisdErrors


from .._misc import _device_list
from .._misc import RUNNER
from .._misc import Service


_DEVICE_STRATEGY = _device_list(1)


class CreateTestCase(unittest.TestCase):
    """
    Test creating a volume w/out a pool.
    """
    _MENU = ['--propagate', 'filesystem', 'create']
    _POOLNAME = 'deadpool'
    _VOLNAMES = ['oubliette', 'mnemosyne']

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

    def testCreation(self):
        """
        Creation of the volume must fail since pool is not specified.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        with self.assertRaises(StratisCliDbusLookupError):
            RUNNER(command_line)


class Create2TestCase(unittest.TestCase):
    """
    Test creating a volume w/ a pool.
    """
    _MENU = ['--propagate', 'filesystem', 'create']
    _POOLNAME = 'deadpool'
    _VOLNAMES = ['oubliette', 'mnemosyne']

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

    def testCreation(self):
        """
        Creation of the volume should succeed since pool is available.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        RUNNER(command_line)


class Create3TestCase(unittest.TestCase):
    """
    Test creating a volume w/ a pool when volume of same name already exists.
    """
    _MENU = ['--propagate', 'filesystem', 'create']
    _POOLNAME = 'deadpool'
    _VOLNAMES = ['oubliette', 'mnemosyne']

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
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        RUNNER(command_line)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testCreation(self):
        """
        Creation of this volume should fail, because there is an existing
        volume of the same name.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        with self.assertRaises(StratisCliRuntimeError) as ctxt:
            RUNNER(command_line)
        self.assertEqual(ctxt.exception.rc, StratisdErrors.ALREADY_EXISTS)
