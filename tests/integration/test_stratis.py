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

from stratis_cli._main import run

from ._misc import Service


class StratisTestCase(unittest.TestCase):
    """
    Test meta information about stratisd.
    """
    _MENU = ['stratis']

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

    def testStratisVersion(self):
        """
        Getting version should just succeed.
        """
        command_line = self._MENU + ['--version']
        all(run(command_line))

    def testStratisLogLevel(self):
        """
        Getting log level should just succeed.
        """
        command_line = self._MENU + ['--log-level']
        all(run(command_line))

    def testStratisNoOptions(self):
        """
        Exactly one option should be set, so this should fail.
        """
        command_line = self._MENU
        with self.assertRaises(SystemExit):
            all(run(command_line))

    def testStratisTwoOptons(self):
        """
        Exactly one option should be set, so this should fail.
        """
        command_line = self._MENU + ['--log-level', '--version']
        with self.assertRaises(SystemExit):
            all(run(command_line))
