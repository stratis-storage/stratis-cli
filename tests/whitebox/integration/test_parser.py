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
    Test parser behavior. The behavior should be identical, regardless of
    whether the "--propagate" flag is set. That is, stratis should never produce
    exception chains because of parser errors. The exception chains should only
    be produced when the "--propagate" flag is set and when an error occurs
    during an action.
    """

    @unittest.expectedFailure
    def testStratisNoSubcommand(self):
        """
        If missing subcommand, or missing "daemon" subcommand return exit code
        of 2. There can't be a missing subcommand for "blockdev", "pool", or
        "filesystem" subcommand, since these default to "list" if no subcommand.

        This fails at this time, see issue:
        https://github.com/stratis-storage/stratis-cli/issues/248
        """
        for command_line in [[], ["daemon"]]:
            for prefix in [[], ["--propagate"]]:
                with self.assertRaises(SystemExit) as context:
                    RUNNER(prefix + command_line)
                exit_code = context.exception.code
                self.assertEqual(exit_code, 2)

    def testStratisTwoOptions(self):
        """
        Exactly one option should be set, so this should fail,
        but only because redundancy accepts no arguments.
        """
        for prefix in [[], ["--propagate"]]:
            command_line = ["daemon", "redundancy", "version"]
            with self.assertRaises(SystemExit) as context:
                RUNNER(prefix + command_line)
            exit_code = context.exception.code
            self.assertEqual(exit_code, 2)

    def testStratisBadSubcommand(self):
        """
        If an unknown subcommand return exit code of 2.
        """
        for command_line in [
            # pylint: disable=bad-continuation
            ["notasub"],
            ["daemon", "notasub"],
            ["pool", "notasub"],
            ["blockdev", "notasub"],
            ["filesystem", "notasub"],
        ]:
            for prefix in [[], ["--propagate"]]:
                with self.assertRaises(SystemExit) as context:
                    RUNNER(prefix + command_line)
                exit_code = context.exception.code
                self.assertEqual(exit_code, 2)
