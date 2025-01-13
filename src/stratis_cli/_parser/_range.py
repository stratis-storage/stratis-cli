# Copyright 2021 Red Hat, Inc.
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
Definition of filesystem actions to display in the CLI.
"""

# isort: STDLIB
import argparse
import re
import sys

# isort: THIRDPARTY
from justbytes import B, GiB, KiB, MiB, PiB, Range, TiB

_RANGE_RE = re.compile(r"^(?P<magnitude>[0-9]+)(?P<units>([KMGTP]i)?B)$")

_SIZE_SPECIFICATION = (
    "Size must be specified using the format <magnitude><units> where "
    "<magnitude> is a decimal integer value and <units> is any binary "
    'unit specifier in the set "B", "KiB", "MiB", "GiB", "TiB", '
    'and "PiB".'
)


def _unit_map(unit_specifier):
    """
    A simple function that maps a unit_specifier string
    call to a justbytes unit designation.

    :param str unit_specifier: the string
    :returns: the corresponding justbytes units
    :rtype: justbytes.BinaryUnit
    """
    if unit_specifier == "B":
        return B
    if unit_specifier == "KiB":
        return KiB
    if unit_specifier == "MiB":
        return MiB
    if unit_specifier == "GiB":
        return GiB
    if unit_specifier == "TiB":
        return TiB
    if unit_specifier == "PiB":
        return PiB
    assert False, f'Unknown unit specifier "{unit_specifier}"'


def parse_range(values):
    """
    Parse a range value.

    :param str values: string to parse
    """
    match = _RANGE_RE.search(values)
    if match is None:
        raise argparse.ArgumentTypeError(
            f"Ill-formed size specification: {_SIZE_SPECIFICATION}"
        )

    (magnitude, unit) = (match.group("magnitude"), match.group("units"))

    units = _unit_map(unit)

    result = Range(int(magnitude), units)

    assert result.magnitude.denominator == 1

    return result


class RejectAction(argparse.Action):
    """
    Just reject any use of the option.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        raise argparse.ArgumentError(
            self, f"Option {option_string} can not be assigned to or set."
        )


class DefaultAction(argparse.Action):
    """
    Detect if the default value was set.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, self.dest + "_default", False)


def gen_subparsers(parser, command_line):
    """
    Yield all subparser/command_lines pairs for this parser and this prefix
    command line.

    :param parser: an argparse parser
    :param command_line: a prefix command line
    :type command_line: list of str
    """
    yield (parser, command_line)
    for action in (
        action
        for action in parser._actions  # pylint: disable=protected-access
        if isinstance(
            action, argparse._SubParsersAction  # pylint: disable=protected-access
        )
    ):
        for name, subparser in sorted(action.choices.items(), key=lambda x: x[0]):
            yield from gen_subparsers(subparser, command_line + [name])


class PrintHelpAction(argparse.Action):
    """
    Print the help text for every subcommand.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        for subparser, _ in gen_subparsers(parser, []):
            subparser.print_help()
        sys.exit(0)


def ensure_nat(arg):
    """
    Raise error if argument is not an natural number.
    """
    try:
        result = int(arg)
    except Exception as err:
        raise argparse.ArgumentTypeError(
            f"Argument {arg} is not a natural number."
        ) from err

    if result < 0:
        raise argparse.ArgumentTypeError(f"Argument {arg} is not a natural number.")
    return result
