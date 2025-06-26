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
Top level parser for Stratis CLI.
"""

# isort: STDLIB
import argparse
import sys

from .._actions import (
    LogicalActions,
    PhysicalActions,
    PoolActions,
    StratisActions,
    TopActions,
    check_stratisd_version,
)
from .._stratisd_constants import ReportKey
from .._version import __version__
from ._debug import TOP_DEBUG_SUBCMDS
from ._key import KEY_SUBCMDS
from ._logical import LOGICAL_SUBCMDS
from ._physical import PHYSICAL_SUBCMDS
from ._pool import POOL_SUBCMDS


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


def print_help(parser):
    """
    Print help.
    """
    return lambda _: parser.error("missing sub-command")


def _add_groups(parser, groups):
    """
    Make an argument group.
    """
    for name, group in groups:
        new_group = parser.add_argument_group(name, group["description"])
        _add_args(new_group, group.get("args", []))
        _add_mut_ex_args(new_group, group.get("mut_ex_args", []))


def _add_args(parser, args):
    """
    Call subcommand.add_argument() based on args list.

    :param parser: the parser being build
    :param list args: a data structure representing the arguments to be added
    """
    for name, arg in args:
        parser.add_argument(name, **arg)


def _add_mut_ex_args(parser, args):
    """
    Add mutually exclusive arguments for a subcommand.

    :param parser: the parser being build
    :param args: a data structure representing sets of mututally exclusive
                 arguments to be added
    :type args: list of bool * (list of dict)
    """
    for one_is_required, arg_list in args:
        group = parser.add_mutually_exclusive_group(required=one_is_required)
        for name, arg in arg_list:
            group.add_argument(name, **arg)


def add_subcommand(subparser, cmd):
    """
    Add subcommand to a parser based on a subcommand dict.
    """
    name, info = cmd

    parser = subparser.add_parser(
        name,
        help=info["help"],
        aliases=info.get("aliases", []),
    )

    subcmds = info.get("subcmds")
    if subcmds is not None:
        subparsers = parser.add_subparsers(title="subcommands", metavar="")
        for subcmd in subcmds:
            add_subcommand(subparsers, subcmd)

    _add_groups(parser, info.get("groups", []))
    _add_args(parser, info.get("args", []))
    _add_mut_ex_args(parser, info.get("mut_ex_args", []))

    def wrap_func(func):
        if func is None:
            return print_help(parser)

        def wrapped_func(*args):
            check_stratisd_version()
            func(*args)

        return wrapped_func

    parser.set_defaults(func=wrap_func(info.get("func")))


DAEMON_SUBCMDS = [
    (
        "version",
        {
            "help": "version of stratisd daemon",
            "func": StratisActions.list_stratisd_version,
        },
    ),
]

ROOT_SUBCOMMANDS = [
    (
        "pool",
        {
            "help": "Perform General Pool Actions",
            "subcmds": POOL_SUBCMDS,
            "func": PoolActions.list_pools,
        },
    ),
    (
        "blockdev",
        {
            "help": "Commands related to block devices that make up the pool",
            "subcmds": PHYSICAL_SUBCMDS,
            "func": PhysicalActions.list_devices,
        },
    ),
    (
        "filesystem",
        {
            "aliases": ["fs"],
            "help": "Commands related to filesystems allocated from a pool",
            "subcmds": LOGICAL_SUBCMDS,
            "func": LogicalActions.list_volumes,
        },
    ),
    (
        "report",
        {
            "help": "Commands related to reports of the daemon state",
            "func": TopActions.get_report,
            "args": [
                (
                    "report_name",
                    {
                        "default": ReportKey.ENGINE_STATE,
                        "type": ReportKey,
                        "help": "Name of the report to display",
                        "nargs": "?",
                        "choices": list(ReportKey),
                    },
                ),
                (
                    "--no-sort-keys",
                    {
                        "action": "store_true",
                        "help": "Turn off sorting keys when printing result.",
                    },
                ),
            ],
        },
    ),
    (
        "key",
        {
            "help": "Commands related to key operations for encrypted pools",
            "subcmds": KEY_SUBCMDS,
            "func": TopActions.list_keys,
        },
    ),
    (
        "debug",
        {
            "help": "Commands for debugging operations.",
            "subcmds": TOP_DEBUG_SUBCMDS,
        },
    ),
    ("daemon", {"help": "Stratis daemon information", "subcmds": DAEMON_SUBCMDS}),
]

GEN_ARGS = [
    ("--propagate", {"action": "store_true", "help": "Allow exceptions to propagate"}),
    (
        "--unhyphenated-uuids",
        {"action": "store_true", "help": "Display UUIDs in unhyphenated format"},
    ),
]


def gen_parser():
    """
    Make the parser.

    :returns: a fully constructed parser for command-line arguments
    :rtype: ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Stratis Storage Manager", prog="stratis"
    )

    # version is special, it has explicit support in argparse
    parser.add_argument("--version", action="version", version=__version__)

    # --print-all-help is special because it introspects on the parser
    parser.add_argument(
        "--print-all-help", action=PrintHelpAction, help=argparse.SUPPRESS, nargs=0
    )

    _add_args(parser, GEN_ARGS)

    subparsers = parser.add_subparsers(title="subcommands", metavar="")

    for subcmd in ROOT_SUBCOMMANDS:
        add_subcommand(subparsers, subcmd)

    parser.set_defaults(func=print_help(parser))

    return parser
