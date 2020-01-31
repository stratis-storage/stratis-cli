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

# isort: STDLIB
import unittest

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli._error_reporting import StratisCliErrorCodes
from stratis_cli._errors import (
    StratisCliActionError,
    StratisCliEngineError,
    StratisCliPartialChangeError,
)
from stratis_cli._stratisd_constants import StratisdErrors

from .._misc import RUNNER, SimTestCase, check_error, device_name_list

_DEVICE_STRATEGY = device_name_list(1)
ERROR = StratisCliErrorCodes.ERROR


@unittest.skip("Temporarily unable to create multiple filesystems at same time")
class CreateTestCase(SimTestCase):
    """
    Test creating a volume w/out a pool.
    """

    _MENU = ["--propagate", "filesystem", "create"]
    _POOLNAME = "deadpool"
    _VOLNAMES = ["oubliette", "mnemosyne"]

    def testCreation(self):
        """
        Creation of the volume must fail since pool is not specified.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        check_error(
            self,
            StratisCliActionError,
            DbusClientUniqueResultError,
            command_line,
            ERROR,
        )


@unittest.skip("Temporarily unable to create multiple filesystems at same time")
class Create2TestCase(SimTestCase):
    """
    Test creating a volume w/ a pool.
    """

    _MENU = ["--propagate", "filesystem", "create"]
    _POOLNAME = "deadpool"
    _VOLNAMES = ["oubliette", "mnemosyne"]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def testCreation(self):
        """
        Creation of the volume should succeed since pool is available.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        RUNNER(command_line)


@unittest.skip("Temporarily unable to create multiple filesystems at same time")
class Create3TestCase(SimTestCase):
    """
    Test creating a volume w/ a pool when volume of same name already exists.
    """

    _MENU = ["--propagate", "filesystem", "create"]
    _POOLNAME = "deadpool"
    _VOLNAMES = ["oubliette", "mnemosyne"]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
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


class Create4TestCase(SimTestCase):
    """
    Test creating a set of volumes, of which one already exists.
    """

    _MENU = ["--propagate", "filesystem", "create"]
    _POOLNAME = "deadpool"
    _VOLNAMES = ["oubliette", "mnemosyne", "gaia"]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES[0:1]
        RUNNER(command_line)

    def testCreate(self):
        """
        Creation of 2 volumes, of which 1 already exists, must fail.
        There is 1 target resource that would change.
        There is 1 target resource that would not change.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES[0:2]
        check_error(
            self,
            StratisCliActionError,
            StratisCliPartialChangeError,
            command_line,
            ERROR,
        )

    def test2Create(self):
        """
        Creation of 3 volumes, of which 1 already exists, must fail.
        There are multiple (2) target resources that would change.
        There is 1 target resource that would not change.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES[0:3]
        check_error(
            self,
            StratisCliActionError,
            StratisCliPartialChangeError,
            command_line,
            ERROR,
        )


class Create5TestCase(SimTestCase):
    """
    Test creating a set of volumes, of which two already exist.
    """

    _MENU = ["--propagate", "filesystem", "create"]
    _POOLNAME = "deadpool"
    _VOLNAMES = ["oubliette", "mnemosyne", "gaia", "zeus"]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        # Creation of two volumes is split up into two calls to RUNNER,
        # since only one filesystem per request is currently allowed.
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES[0:1]
        RUNNER(command_line)

        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES[1:2]
        RUNNER(command_line)

    def testCreate(self):
        """
        Creation of 3 volumes, of which 2 already exist, must fail.
        There is 1 target resource that would change.
        There are multiple (2) target resources that would not change.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES[0:3]
        check_error(
            self,
            StratisCliActionError,
            StratisCliPartialChangeError,
            command_line,
            ERROR,
        )

    def test2Create(self):
        """
        Creation of 4 volumes, of which 2 already exist, must fail.
        There are multiple (2) target resources that would change.
        There are multiple (2) target resources that would not change.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES[0:4]
        check_error(
            self,
            StratisCliActionError,
            StratisCliPartialChangeError,
            command_line,
            ERROR,
        )
