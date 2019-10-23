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
Test 'rename'.
"""

from dbus_client_gen import DbusClientUniqueResultError
from stratis_cli._errors import StratisCliActionError
from stratis_cli._errors import StratisCliNoChangeError

from .._misc import RUNNER
from .._misc import SimTestCase
from .._misc import device_name_list

_DEVICE_STRATEGY = device_name_list(1)


class Rename1TestCase(SimTestCase):
    """
    Test 'rename' when pool is non-existant.
    """

    _MENU = ["--propagate", "pool", "rename"]
    _POOLNAME = "deadpool"
    _NEW_POOLNAME = "livepool"

    def testRename(self):
        """
        This should fail because original name does not exist.
        """
        command_line = self._MENU + [self._POOLNAME, self._NEW_POOLNAME]
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, DbusClientUniqueResultError)

    def testSameName(self):
        """
        Renaming to itself will fail because the pool does not exist.
        """
        command_line = self._MENU + [self._POOLNAME, self._POOLNAME]
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, DbusClientUniqueResultError)


class Rename2TestCase(SimTestCase):
    """
    Test 'rename' when pool exists.
    """

    _MENU = ["--propagate", "pool", "rename"]
    _POOLNAME = "deadpool"
    _NEW_POOLNAME = "livepool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def testRename(self):
        """
        This should succeed because pool exists.
        """
        command_line = self._MENU + [self._POOLNAME, self._NEW_POOLNAME]
        RUNNER(command_line)

    def testSameName(self):
        """
        This should fail, because this performs no action.
        """
        command_line = self._MENU + [self._POOLNAME, self._POOLNAME]
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliNoChangeError)

    def testNonExistentPool(self):
        """
        This should fail, because this pool is not there.
        """
        command_line = self._MENU + ["nopool", self._POOLNAME]
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, DbusClientUniqueResultError)
