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

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliActionError, StratisCliEngineError
from stratis_cli._stratisd_constants import StratisdErrors

from .._misc import RUNNER, SimTestCase, check_error, device_name_list

_DEVICE_STRATEGY = device_name_list(1)


class Destroy1TestCase(SimTestCase):
    """
    Test 'destroy' on empty database.

    'destroy' should always fail if pool is missing.
    """

    _MENU = ["--propagate", "pool", "destroy"]
    _POOLNAME = "deadpool"

    def testExecution(self):
        """
        Destroy should fail because there is no object path for the pool.
        """
        command_line = self._MENU + [self._POOLNAME]
        check_error(
            self,
            StratisCliActionError,
            DbusClientUniqueResultError,
            command_line,
            StratisCliErrorCodes.ERROR,
        )


class Destroy2TestCase(SimTestCase):
    """
    Test 'destroy' on database which contains the given pool.
    """

    _MENU = ["--propagate", "pool", "destroy"]
    _POOLNAME = "deadpool"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def testExecution(self):
        """
        The pool was just created, so must be destroyable.
        """
        command_line = self._MENU + [self._POOLNAME]
        RUNNER(command_line)


class Destroy3TestCase(SimTestCase):
    """
    Test 'destroy' on database which contains the given pool with a volume.
    """

    _MENU = ["--propagate", "pool", "destroy"]
    _POOLNAME = "deadpool"
    _VOLNAME = "vol"

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        command_line = ["filesystem", "create", self._POOLNAME, self._VOLNAME]
        RUNNER(command_line)

    def testExecution(self):
        """
        This should fail since it has a filesystem.
        """
        command_line = self._MENU + [self._POOLNAME]
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)
        cause = context.exception.__cause__
        self.assertIsInstance(cause, StratisCliEngineError)
        self.assertEqual(cause.rc, StratisdErrors.BUSY)

    def testWithFilesystemRemoved(self):
        """
        This should succeed since the filesystem is removed first.
        """
        command_line = ["filesystem", "destroy", self._POOLNAME, self._VOLNAME]
        RUNNER(command_line)
        command_line = self._MENU + [self._POOLNAME]
        RUNNER(command_line)
