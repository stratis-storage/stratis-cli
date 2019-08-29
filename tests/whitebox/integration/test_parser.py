# Copyright 2019 Red Hat, Inc.
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
Test command-line argument parsing.
"""

import unittest

from ._misc import RUNNER


class ParserTestCase(unittest.TestCase):
    """
    Test parser behavior
    """

    _MENU = ["--propagate", "daemon"]

    def testStratisNoOptions(self):
        """
        Exactly one option should be set, this should succeed, but print help.
        """
        command_line = self._MENU
        RUNNER(command_line)

    def testStratisTwoOptions(self):
        """
        Exactly one option should be set, so this should fail,
        but only because redundancy accepts no arguments.
        """
        command_line = self._MENU + ["redundancy", "version"]
        with self.assertRaises(SystemExit):
            RUNNER(command_line)
