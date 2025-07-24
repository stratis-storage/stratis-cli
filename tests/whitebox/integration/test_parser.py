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

    def _do_test(self, command_line):
        for prefix in [[], ["--propagate"]]:
            self.check_system_exit(prefix + command_line, _PARSE_ERROR)

    def test_stratis_no_subcommand(self):
        """
        If missing subcommand, or missing "daemon" subcommand return exit code
        of 2. There can't be a missing subcommand for "blockdev", "pool", or
        "filesystem" subcommand, since these default to "list" if no subcommand.
        """
        for command_line in [[], ["daemon"]]:
            self._do_test(command_line)

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
            self._do_test(command_line)

    def test_nonexistent_report(self):
        """
        Test getting nonexistent report.
        """
        self._do_test(["report", "notreport"])

    def test_negative_filesystem_limit(self):
        """
        Verify that a negative integer filesystem limit is rejected.
        """
        self._do_test(["pool", "set-fs-limit", "thispool", "-1"])

    def test_non_integer_filesystem_limit(self):
        """
        Verify that a non_integer filesystem limit is rejected.
        """
        self._do_test(["pool", "set-fs-limit", "thispool", "1.2"])

    def test_invalid_overprovision_value(self):
        """
        Overprovision command only accepts yes or no.
        """
        self._do_test(["pool", "overprovision", "thispool", "1.2"])

    def test_explain_non_existent_code(self):
        """
        Verify parser error on bogus pool code.
        """
        self._do_test(["pool", "explain", "bogus"])

    def test_stratis_list_filesystem_with_name_no_pool(self):
        """
        We want to get a parse error if filesystem UUID is specified but no
        name.
        """
        self._do_test(["fs", "list", "--name=bogus"])

    def test_stratis_list_filesystem_with_post_parser_1(self):
        """
        Verify that parser error is returned if unsettable option is assigned.
        """
        self._do_test(["fs", "list", "--post-parser=no"])

    def test_stratis_list_filesystem_with_post_parser_2(self):
        """
        Verify that parser error is returned if unsettable option is set.
        """
        self._do_test(["fs", "list", "--post-parser"])


class TestFilesystemSizeParsing(ParserTestCase):
    """
    Test that parser errors are properly returned on badly formatted sizes.
    """

    def _do_filesystem_create_test(self, size_args):
        self._do_test(["filesystem", "create", "pn", "fn"] + size_args)

    def test_integer_magnitude(self):
        """
        Verify that a parse error occurs if the size magnitude is not an
        integer.
        """
        self._do_filesystem_create_test(['--size="32.2GiB"'])

    def test_gibberish_magnitude(self):
        """
        Verify that a parse error occurs if the size magnitude is not a number.
        """
        self._do_filesystem_create_test(['--size="carbonGiB"'])

    def test_extra_space(self):
        """
        Verify no spaces allowed between magnitude and units.
        """
        self._do_filesystem_create_test(['--size="312 GiB"'])

    def test_funny_units(self):
        """
        Verify no funny units allowed.
        """
        self._do_filesystem_create_test(['--size="312WiB"'])

    def test_decimal_units(self):
        """
        Verify no decimal units allowed.
        """
        self._do_filesystem_create_test(['--size="312GB"'])

    def test_empty_units(self):
        """
        Verify units specification is mandatory.
        """
        self._do_filesystem_create_test(['--size="312"'])


class TestFilesystemSizeLimitParsing(ParserTestCase):
    """
    Test that parser errors are properly returned on selected badly formatted
    size limits.
    """

    def test_size_limit_string(self):
        """
        Verify that a parse error occurs if the size limit is a string that is
        not "current".
        """
        self._do_test(["filesystem", "set-size-limit", "pn", "fn", "buckle"])


class TestBadlyFormattedUuid(ParserTestCase):
    """
    Test that parser errors are properly returned on badly formatted UUIDs.
    """

    def test_bad_uuid_pool(self):
        """
        Test badly formatted pool UUID.
        """
        self._do_test(["pool", "debug", "get-object-path", "--uuid=not"])

    def test_bad_uuid_filesystem(self):
        """
        Test badly formatted filesystem UUID.
        """
        self._do_test(["filesystem", "debug", "get-object-path", "--uuid=not"])

    def test_bad_uuid_blockdev(self):
        """
        Test badly formatted blockdev UUID.
        """
        self._do_test(["blockdev", "debug", "get-object-path", "--uuid=not"])

    def test_bad_uuid_blockdev_2(self):
        """
        Test badly formed UUID for blockdev on extend-data.
        """
        self._do_test(["pool", "extend-data", "poolname", "--device-uuid=not"])

    def test_bad_uuid_metadata(self):
        """
        Test badly formed UUID for get-metadata.
        """
        self._do_test(["pool", "debug", "get-metadata", "--uuid=not"])


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


class TestClevisOptions(ParserTestCase):
    """
    Verify that invalid clevis encryption options are detected.
    """

    def _do_clevis_test(self, clevis_args):
        """
        Apply clevis args to create command_line and verify parser error.
        """
        for subcommand in [
            ["pool", "create", "pn", "/dev/n"],
            ["pool", "encryption", "on", "--name=pn"],
        ]:
            self._do_test(subcommand + clevis_args)

    def test_create_with_clevis_1(self):
        """
        Test parsing when creating a pool w/ clevis tang but no URL.
        """
        self._do_clevis_test(["--clevis=tang"])

    def test_create_with_clevis_2(self):
        """
        Test parsing when creating a pool w/ clevis tang, a URL, but no
        thumbprint or trust-url.
        """
        self._do_clevis_test(["--clevis=tang", "--tang-url=url"])

    def test_create_with_clevis_3(self):
        """
        Test parsing when creating a pool w/ clevis tang, a URL, but both
        thumbprint and --trust-url set.
        """
        self._do_clevis_test(
            ["--clevis=tang", "--tang-url=url", "--thumbprint=jkj", "--trust-url"]
        )

    def test_create_with_url_no_modifier(self):
        """
        Parser should exit if created with --tang-url specified but not
        modifiers as that will result in a pool without encryption being
        created.
        """
        self._do_clevis_test(["--tang-url=url"])

    def test_create_with_thumbprint_no_url(self):
        """
        Parser should exit if --thumbprint option is set and no URL specified.
        """
        self._do_clevis_test(["--thumbprint=xyz"])

    def test_create_with_trust_no_url(self):
        """
        Parser should exit if --trust-url option is set and no URL specified.
        """
        self._do_clevis_test(["--trust-url"])

    def test_create_with_url_no_clevis(self):
        """
        Parser should exit if created with --tang-url specified but not
        --clevis=tang as that will result in a pool without encryption being
        created.
        """
        self._do_clevis_test(["--tang-url=url", "--trust-url"])

    def test_create_with_post_parser_set(self):
        """
        Verify that setting the --post-parser option will always result in
        failure on pool creation.
        """
        self._do_clevis_test(["--clevis=tpm2", "--post-parser=yes"])


class TestCreateIntegrityOptions(ParserTestCase):
    """
    Verify that invalid integrity create options are detected.
    """

    def _do_integrity_test(self, integrity_args):
        """
        Apply integrity args to create command_line and verify parser error.
        """
        self._do_test(["pool", "create", "pn", "/dev/n"] + integrity_args)

    def test_create_with_bad_tag_value(self):
        """
        Verify that an unrecognized tag value causes an error.
        """
        self._do_integrity_test(["--tag-spec=512"])

    def test_create_with_integrity_no_journal_size(self):
        """
        Verify that creating with integrity = no plus good journal-size
        results in a parse error.
        """
        self._do_integrity_test(["--integrity=no", "--journal-size=128MiB"])

    def test_create_with_integrity_no_tag_spec(self):
        """
        Verify that creating with integrity = no plus good tag-size
        results in a parse error.
        """
        self._do_integrity_test(["--integrity=no", "--tag-spec=32b"])
