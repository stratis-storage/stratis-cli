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

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import (
    StratisCliMissingClevisTangURLError,
    StratisCliMissingClevisThumbprintError,
)

from ._misc import RUNNER, RunTestCase, SimTestCase

_PARSE_ERROR = StratisCliErrorCodes.PARSE_ERROR


class ParserTestCase(RunTestCase):
    """
    Test parser behavior. The behavior should be identical, regardless of
    whether the "--propagate" flag is set. That is, stratis should never produce
    exception chains because of parser errors. The exception chains should only
    be produced when the "--propagate" flag is set and when an error occurs
    during an action.
    """

    def test_stratis_no_subcommand(self):
        """
        If missing subcommand, or missing "daemon" subcommand return exit code
        of 2. There can't be a missing subcommand for "blockdev", "pool", or
        "filesystem" subcommand, since these default to "list" if no subcommand.
        """
        for command_line in [[], ["daemon"]]:
            for prefix in [[], ["--propagate"]]:
                self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_stratis_two_options(self):
        """
        Exactly one option should be set, so this should fail,
        but only because redundancy accepts no arguments.
        """
        for prefix in [[], ["--propagate"]]:
            command_line = ["daemon", "redundancy", "version"]
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_stratis_bad_subcommand(self):
        """
        If an unknown subcommand return exit code of 2.
        """
        for command_line in [
            ["notasub"],
            ["daemon", "notasub"],
            ["pool", "notasub"],
            ["blockdev", "notasub"],
            ["filesystem", "notasub"],
        ]:
            for prefix in [[], ["--propagate"]]:
                self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_redundancy(self):
        """
        Verify that there is a parser error if redundancy is not "none" in
        pool creation.
        """
        command_line = [
            "pool",
            "create",
            "--redundancy",
            "raid6",
            "the_pool",
            "a_blockdev",
            "another_blockdev",
        ]

        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_nonexistent_report(self):
        """
        Test getting nonexistent report.
        """
        command_line = ["report", "notreport"]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_clevis_1(self):
        """
        Test parsing when creating a pool w/ clevis tang, a URL, but both
        thumbprint and --trust-url set.
        """
        command_line = [
            "pool",
            "create",
            "--clevis=tang",
            "--tang-url=url",
            "--thumbprint=jkj",
            "--trust-url",
            "pn",
            "/dev/n",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)


class ParserSimTestCase(SimTestCase):
    """
    Parser tests which require the sim engine to be running.

    Includes tests which are not strictly parser errors, i.e., where the
    command-line is grammatical, but the command is simply invalid.
    """

    def test_stratis_list_default(self):
        """
        Verify that pool, filesystem, and blockdev subcommands execute
        without any additional command.
        """
        for subcommand in [["pool"], ["filesystem"], ["blockdev"]]:
            for prefix in [[], ["--propagate"]]:
                self.assertEqual(RUNNER(prefix + subcommand), 0)

    def test_create_with_clevis_1(self):
        """
        Test parsing when creating a pool w/ clevis tang but no URL.
        """
        command_line = [
            "--propagate",
            "pool",
            "create",
            "--clevis=tang",
            "pn",
            "/dev/n",
        ]
        self.check_error(StratisCliMissingClevisTangURLError, command_line, 1)

    def test_create_with_clevis_2(self):
        """
        Test parsing when creating a pool w/ clevis tang, a URL, but no
        thumbprint or trust-url.
        """
        command_line = [
            "--propagate",
            "pool",
            "create",
            "--clevis=tang",
            "--tang-url=url",
            "pn",
            "/dev/n",
        ]
        self.check_error(StratisCliMissingClevisThumbprintError, command_line, 1)
