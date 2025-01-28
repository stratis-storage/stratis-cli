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

# isort: STDLIB
from io import StringIO
from unittest import mock

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes

from ._misc import RUNNER, RunTestCase, SimTestCase

_PARSE_ERROR = StratisCliErrorCodes.PARSE_ERROR


class ParserTestCase(RunTestCase):  # pylint: disable=too-many-public-methods
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

    def test_nonexistent_report(self):
        """
        Test getting nonexistent report.
        """
        command_line = ["report", "notreport"]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_negative_filesystem_limit(self):
        """
        Verify that a negative integer filesystem limit is rejected.
        """
        command_line = ["pool", "set-fs-limit", "thispool", "-1"]
        for prefix in [[], ["-propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_non_integer_filesystem_limit(self):
        """
        Verify that a non_integer filesystem limit is rejected.
        """
        command_line = ["pool", "set-fs-limit", "thispool", "1.2"]
        for prefix in [[], ["-propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_invalid_overprovision_value(self):
        """
        Overprovision command only accepts yes or no.
        """
        command_line = ["pool", "overprovision", "thispool", "1.2"]
        for prefix in [[], ["-propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_explain_non_existent_code(self):
        """
        Verify parser error on bogus pool code.
        """
        command_line = ["pool", "explain", "bogus"]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_clevis_1(self):
        """
        Test parsing when creating a pool w/ clevis tang but no URL.
        """
        command_line = [
            "pool",
            "create",
            "pn",
            "/dev/n",
            "--clevis=tang",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_clevis_2(self):
        """
        Test parsing when creating a pool w/ clevis tang, a URL, but no
        thumbprint or trust-url.
        """
        command_line = [
            "pool",
            "create",
            "pn",
            "/dev/n",
            "--clevis=tang",
            "--tang-url=url",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_clevis_3(self):
        """
        Test parsing when creating a pool w/ clevis tang, a URL, but both
        thumbprint and --trust-url set.
        """
        command_line = [
            "pool",
            "create",
            "pn",
            "/dev/n",
            "--clevis=tang",
            "--tang-url=url",
            "--thumbprint=jkj",
            "--trust-url",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_url_no_modifier(self):
        """
        Parser should exit if created with --tang-url specified but not
        modifiers as that will result in a pool without encryption being
        created.
        """
        command_line = [
            "pool",
            "create",
            "pn",
            "/dev/n",
            "--tang-url=url",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_thumbprint_no_url(self):
        """
        Parser should exit if --thumbprint option is set and no URL specified.
        """
        command_line = [
            "pool",
            "create",
            "pn",
            "/dev/n",
            "--thumbprint=xyz",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_trust_no_url(self):
        """
        Parser should exit if --trust-url option is set and no URL specified.
        """
        command_line = [
            "pool",
            "create",
            "pn",
            "/dev/n",
            "--trust-url",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_url_no_clevis(self):
        """
        Parser should exit if created with --tang-url specified but not
        --clevis=tang as that will result in a pool without encryption being
        created.
        """
        command_line = [
            "pool",
            "create",
            "pn",
            "/dev/n",
            "--tang-url=url",
            "--trust-url",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_post_parser_set(self):
        """
        Verify that setting the --post-parser option will always result in
        failure on pool creation.
        """
        command_line = [
            "pool",
            "create",
            "pn",
            "/dev/n",
            "--clevis=tpm2",
            "--post-parser=yes",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_bad_tag_value(self):
        """
        Verify that an unrecognized tag value causes an error.
        """
        command_line = [
            "pool",
            "create",
            "pn",
            "/dev/n",
            "--tag-spec=512",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_integrity_no_journal_size(self):
        """
        Verify that creating with integrity = no plus good journal-size
        results in a parse error.
        """
        command_line = [
            "pool",
            "create",
            "pn",
            "/dev/n",
            "--integrity=no",
            "--journal-size=128MiB",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_create_with_integrity_no_tag_spec(self):
        """
        Verify that creating with integrity = no plus good tag-size
        results in a parse error.
        """
        command_line = [
            "pool",
            "create",
            "pn",
            "/dev/n",
            "--integrity=no",
            "--tag-spec=32b",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_stratis_list_filesystem_with_name_no_pool(self):
        """
        We want to get a parse error if filesystem UUID is specified but no
        name.
        """
        command_line = ["fs", "list", "--name=bogus"]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_stratis_list_filesystem_with_post_parser_1(self):
        """
        Verify that parser error is returned if unsettable option is assigned.
        """
        command_line = ["fs", "list", "--post-parser=no"]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_stratis_list_filesystem_with_post_parser_2(self):
        """
        Verify that parser error is returned if unsettable option is set.
        """
        command_line = ["fs", "list", "--post-parser"]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)


class TestFilesystemSizeParsing(RunTestCase):
    """
    Test that parser errors are properly returned on badly formatted sizes.
    """

    def test_integer_magnitude(self):
        """
        Verify that a parse error occurs if the size magnitude is not an
        integer.
        """
        command_line = ["filesystem", "create", "pn", "fn", '--size="32.2GiB"']
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_gibberish_magnitude(self):
        """
        Verify that a parse error occurs if the size magnitude is not a number.
        """
        command_line = ["filesystem", "create", "pn", "fn", '--size="carbonGiB"']
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_extra_space(self):
        """
        Verify no spaces allowed between magnitude and units.
        """
        command_line = ["filesystem", "create", "pn", "fn", '--size="312 GiB"']
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_funny_units(self):
        """
        Verify no funny units allowed.
        """
        command_line = ["filesystem", "create", "pn", "fn", '--size="312WiB"']
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_decimal_units(self):
        """
        Verify no decimal units allowed.
        """
        command_line = ["filesystem", "create", "pn", "fn", '--size="312GB"']
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_empty_units(self):
        """
        Verify units specification is mandatory.
        """
        command_line = ["filesystem", "create", "pn", "fn", '--size="312"']
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)


class TestFilesystemSizeLimitParsing(RunTestCase):
    """
    Test that parser errors are properly returned on selected badly formatted
    size limits.
    """

    def test_size_limit_string(self):
        """
        Verify that a parse error occurs if the size limit is a string that is
        not "current".
        """
        command_line = [
            "filesystem",
            "set-size-limit",
            "pn",
            "fn",
            "buckle",
        ]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)


class TestBadlyFormattedUuid(RunTestCase):
    """
    Test that parser errors are properly returned on badly formatted UUIDs.
    """

    def test_bad_uuid_pool(self):
        """
        Test badly formatted pool UUID.
        """
        command_line = ["pool", "debug", "get-object-path", "--uuid=not"]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_bad_uuid_filesystem(self):
        """
        Test badly formatted filesystem UUID.
        """
        command_line = ["filesystem", "debug", "get-object-path", "--uuid=not"]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_bad_uuid_blockdev(self):
        """
        Test badly formatted blockdev UUID.
        """
        command_line = ["blockdev", "debug", "get-object-path", "--uuid=not"]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_bad_uuid_blockdev_2(self):
        """
        Test badly formed UUID for blockdev on extend-data.
        """
        command_line = ["pool", "extend-data", "poolname", "--device-uuid=not"]
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_bad_uuid_metadata(self):
        """
        Test badly formed UUID for get-metadata.
        """
        command_line = ["pool", "debug", "get-metadata", "--uuid=not"]
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


class TestAllHelp(RunTestCase):
    """
    Verify that --print-all-help option succeeds.
    """

    def test_print_all_help(self):
        """
        Test the --print-all-help option.
        """
        with mock.patch("sys.stdout", new=StringIO()):
            self.check_system_exit(["--print-all-help"], 0)
