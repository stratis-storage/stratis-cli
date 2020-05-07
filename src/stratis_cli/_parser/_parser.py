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
    StratisActions,
    TopActions,
    check_stratisd_version,
)
from .._version import __version__
from ._logical import LOGICAL_SUBCMDS
from ._physical import PHYSICAL_SUBCMDS
from ._pool import POOL_SUBCMDS

PRINT_HELP = lambda parser: lambda _: parser.error("missing sub-command")


def _add_args(parser, args):
    """
    Call subcommand.add_argument() based on args list.

    :param parser: the parser being build
    :param list args: a data structure representing the arguments to be added
    """
    for name, arg in args:
        parser.add_argument(name, **arg)


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

    def wrap_func(func):
        if func is None:
            return PRINT_HELP(parser)

        def wrapped_func(*args):
            check_stratisd_version()
            func(*args)

        return wrapped_func

    parser.set_defaults(func=wrap_func(info.get("func", None)))


DAEMON_SUBCMDS = [
    (
        "redundancy",
        dict(
            help="Redundancy designations understood by stratisd daemon",
            func=StratisActions.list_stratisd_redundancy,
        ),
    ),
    (
        "version",
        dict(
            help="version of stratisd daemon", func=StratisActions.list_stratisd_version
        ),
    ),
]

ROOT_SUBCOMMANDS = [
    (
        "pool",
        dict(
            help="Perform General Pool Actions",
            subcmds=POOL_SUBCMDS,
            func=TopActions.list_pools,
        ),
    ),
    (
        "blockdev",
        dict(
            help="Commands related to block devices that make up the pool",
            subcmds=PHYSICAL_SUBCMDS,
            func=PhysicalActions.list_devices,
        ),
    ),
    (
        "filesystem",
        dict(
            aliases=["fs"],
            help="Commands related to filesystems allocated from a pool",
            subcmds=LOGICAL_SUBCMDS,
            func=LogicalActions.list_volumes,
        ),
    ),
    ("daemon", dict(help="Stratis daemon information", subcmds=DAEMON_SUBCMDS)),
]

GEN_ARGS = [
    ("--propagate", dict(action="store_true", help="Allow exceptions to propagate"))
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

    parser.set_defaults(func=PRINT_HELP(parser))

    return parser
