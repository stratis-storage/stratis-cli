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


def print_help(parser):
    """
    Print help.
    """
    return lambda _: parser.error("missing sub-command")


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
    Add mututally exlusive arguments for a subcommand.

    :param parser: the parser being build
    :param args: a data structure representing sets of mututally exclusive
                 arguments to be added
    :type args: list of bool * (list of dict)
    """
    for (one_is_required, arg_list) in args:
        group = parser.add_mutually_exclusive_group(required=one_is_required)
        for name, arg in arg_list:
            group.add_argument(name, **arg)


def add_subcommand(subparser, cmd):
    """
    Add subcommand to a parser based on a subcommand dict.
    """
    name, info = cmd
    parser = subparser.add_parser(
        name, help=info["help"], aliases=info.get("aliases", [])
    )

    subcmds = info.get("subcmds")
    if subcmds is not None:
        subparsers = parser.add_subparsers(title="subcommands")
        for subcmd in subcmds:
            add_subcommand(subparsers, subcmd)

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
                        "default": "engine_state_report",
                        "type": str,
                        "help": ("Name of the report to display"),
                        "nargs": "?",
                        "choices": [str(x) for x in list(ReportKey)],
                    },
                )
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

    _add_args(parser, GEN_ARGS)

    subparsers = parser.add_subparsers(title="subcommands")

    for subcmd in ROOT_SUBCOMMANDS:
        add_subcommand(subparsers, subcmd)

    parser.set_defaults(func=print_help(parser))

    return parser
