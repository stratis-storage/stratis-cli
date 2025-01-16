# Copyright 2025 Red Hat, Inc.
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
Test that printing out help text does not result in any error returns or
exceptions.
"""

# isort: STDLIB
from argparse import _SubParsersAction

# isort: LOCAL
from stratis_cli._parser import gen_parser

from ._misc import RunTestCase


def gen_subcommands(parser, command_line):
    """
    Recursively traverse the parser, yielding all possible subcommands.
    """
    yield command_line
    for action in (
        action
        for action in parser._actions  # pylint: disable=protected-access
        if isinstance(action, _SubParsersAction)
    ):
        for name, subparser in action.choices.items():
            yield from gen_subcommands(subparser, command_line + [name])


class ParserHelpTestCase(RunTestCase):
    """
    Test various timeout inputs.
    """

    def test_help(self):
        """
        Test all parser help.
        """

        for command_line in gen_subcommands(gen_parser(), []):
            self.check_system_exit(command_line + ["--help"], 0)
