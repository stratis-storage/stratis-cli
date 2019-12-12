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

# isort: LOCAL
from stratis_cli._errors import (
    StratisCliActionError,
    StratisCliInUseSameTierError,
    StratisCliNameConflictError,
)

from .._misc import RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(1)
_DEVICE_STRATEGY_2 = device_name_list(2)


class CreateTestCase(SimTestCase):
    """
    Test 'create' parsing.
    """

    _MENU = ["--propagate", "pool", "create"]
    _POOLNAME = "deadpool"

    def testRedundancy(self):
        """
        Parser error on all redundancy that is not 'none'.
        """
        command_line = (
            self._MENU + ["--redundancy", "raid6", self._POOLNAME] + _DEVICE_STRATEGY()
        )
        with self.assertRaises(SystemExit):
            RUNNER(command_line)


class Create3TestCase(SimTestCase):
    """
    Test 'create' on name collision.
    """

    _MENU = ["--propagate", "pool", "create"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        self.devices = _DEVICE_STRATEGY()
        command_line = ["pool", "create", self._POOLNAME] + self.devices
        RUNNER(command_line)

    def testCreateSameDevices(self):
        """
        Create should fail with a StratisCliNameConflictError trying to create
        new pool with the same devices and the same name as previous.
        """
        command_line = self._MENU + [self._POOLNAME] + self.devices
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliNameConflictError)
        self.assertNotEqual(str(cause), "")

    def testCreateDifferentDevices(self):
        """
        Create should fail with a StratisCliNameConflictError trying to create
        new pool with different devices and the same name as previous.
        """
        command_line = self._MENU + [self._POOLNAME] + _DEVICE_STRATEGY()
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliNameConflictError)
        self.assertNotEqual(str(cause), "")


class Create4TestCase(SimTestCase):
    """
    Test adding data devices to two pools.
    """

    _POOLNAME_1 = "deadpool1"
    _POOLNAME_2 = "deadpool2"
    _MENU = ["--propagate", "pool", "create"]
    _DEVICES = _DEVICE_STRATEGY_2()

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME_1] + self._DEVICES
        RUNNER(command_line)

    def testCreateSameDevices(self):
        """
        Test that creating two pools with different names and the same devices raises
        a StratisCliInUseSameTierError exception.
        """
        command_line = self._MENU + [self._POOLNAME_2] + self._DEVICES
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliInUseSameTierError)
        self.assertNotEqual(str(cause), "")
