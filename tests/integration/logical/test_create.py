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

from dbus_client_gen import DbusClientUniqueResultError

from stratis_cli._errors import StratisCliActionError
from stratis_cli._errors import StratisCliEngineError

from stratis_cli._stratisd_constants import StratisdErrors

from .._misc import device_name_list
from .._misc import RUNNER
from .._misc import SimTestCase

_DEVICE_STRATEGY = device_name_list(1)


@unittest.skip(
    "Temporarily unable to create multiple filesystems at same time")
class CreateTestCase(SimTestCase):
    """
    Test creating a volume w/out a pool.
    """
    _MENU = ['--propagate', 'filesystem', 'create']
    _POOLNAME = 'deadpool'
    _VOLNAMES = ['oubliette', 'mnemosyne']

    def testCreation(self):
        """
        Creation of the volume must fail since pool is not specified.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, DbusClientUniqueResultError)


@unittest.skip(
    "Temporarily unable to create multiple filesystems at same time")
class Create2TestCase(SimTestCase):
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
        super().setUp()
        command_line = ['pool', 'create', self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def testCreation(self):
        """
        Creation of the volume should succeed since pool is available.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        RUNNER(command_line)


@unittest.skip(
    "Temporarily unable to create multiple filesystems at same time")
class Create3TestCase(SimTestCase):
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
        super().setUp()
        command_line = ['pool', 'create', self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        RUNNER(command_line)

    def testCreation(self):
        """
        Creation of this volume should fail, because there is an existing
        volume of the same name.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        with self.assertRaises(StratisCliEngineError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliEngineError)
        self.assertEqual(cause.rc, StratisdErrors.ALREADY_EXISTS)
