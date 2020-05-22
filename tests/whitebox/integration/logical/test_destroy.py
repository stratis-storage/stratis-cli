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

# isort: STDLIB
import unittest

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientUniqueResultError

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliPartialChangeError

from .._misc import RUNNER, SimTestCase, device_name_list

_DEVICE_STRATEGY = device_name_list(1)
_ERROR = StratisCliErrorCodes.ERROR


class Destroy4TestCase(SimTestCase):
    """
    Test destroying a set of volumes, of which one does not exist.
    """

    _MENU = ["--propagate", "filesystem", "destroy"]
    _POOLNAME = "deadpool"
    _VOLNAMES = ["oubliette", "mnemosyne"]

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

        command_line = ["filesystem", "create", self._POOLNAME] + self._VOLNAMES[0:1]
        RUNNER(command_line)

    def test_destroy(self):
        """
        Destruction of 2 volumes, of which 1 does not exist, must fail.
        There is 1 target resource that would change.
        There is 1 target resource that would not change.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        self.check_error(StratisCliPartialChangeError, command_line, _ERROR)

    def test_2_destroy(self):
        """
        Destruction of 3 volumes, of which 1 does not exist, must fail.
        There are multiple (2) target resources that would change.
        There is 1 target resource that would not change.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES[0:3]
        self.check_error(StratisCliPartialChangeError, command_line, _ERROR)


class Create5TestCase(SimTestCase):
    """
    Test destroying a set of volumes, of which two do not exist.
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

    def test_destroy(self):
        """
        Destruction of 3 volumes, of which 2 do not exist, must fail.
        There is 1 target resource that would change.
        There are multiple (2) target resources that would not change.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES[0:3]
        self.check_error(StratisCliPartialChangeError, command_line, _ERROR)

    def test_2_destroy(self):
        """
        Destruction of 4 volumes, of which 2 do not exist, must fail.
        There are multiple (2) target resources that would change.
        There are multiple (2) target resources that would not change.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES[0:4]
        self.check_error(StratisCliPartialChangeError, command_line, _ERROR)
