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


import argparse

from .._actions import StratisActions

from .._version import __version__

from ._logical import build_logical_parser
from ._physical import build_physical_parser
from ._pool import build_pool_parser


def build_daemon_parser(parser):
    """
    Generates the parser appropriate for obtaining information about stratisd.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for obtaining information about stratisd
    :rtype: ArgumentParser
    """
    subparsers = \
       parser.add_subparsers(dest='subparser_name', title='subcommands')

    redundancy_parser = subparsers.add_parser(
       'redundancy',
       description="redundancy designations understood by stratisd daemon"
    )
    redundancy_parser.set_defaults(func=StratisActions.list_stratisd_redundancy)

    version_parser = subparsers.add_parser(
       'version',
       description="version of stratisd daemon"
    )
    version_parser.set_defaults(func=StratisActions.list_stratisd_version)

    return parser


_SUBPARSER_TABLE = {
   'blockdev' : build_physical_parser,
   'filesystem' : build_logical_parser,
   'pool' : build_pool_parser,
   'daemon' : build_daemon_parser
}


def gen_parser():
    """
    Make the parser.

    :returns: a fully constructed parser for command-line arguments
    :rtype: ArgumentParser
    """
    parser = argparse.ArgumentParser(
       description="Stratis Storage Manager",
       prog='stratis'
    )

    parser.add_argument(
       '--version',
       action='version',
       version=__version__
    )

    parser.add_argument(
       '--propagate',
       action='store_true',
       help='allow exceptions to propagate'
    )

    subparsers = \
       parser.add_subparsers(dest='subparser_name', title='subcommands')

    subparser_table = dict()

    subparser_table['blockdev'] = \
       subparsers.add_parser(
          'blockdev',
          description="Administer Blockdev Aspects of Specified Pool"
       )
    _SUBPARSER_TABLE['blockdev'](subparser_table['blockdev'])

    subparser_table['filesystem'] = \
       subparsers.add_parser(
          'filesystem',
          description="Administer Filesystems Aspects of Specified Pool"
       )
    _SUBPARSER_TABLE['filesystem'](subparser_table['filesystem'])

    subparser_table['pool'] = \
       subparsers.add_parser('pool', description="Perform General Pool Actions")
    _SUBPARSER_TABLE['pool'](subparser_table['pool'])

    subparser_table['daemon'] = \
       subparsers.add_parser(
          'daemon',
          description="Stratis daemon information"
    )
    _SUBPARSER_TABLE['daemon'](subparser_table['daemon'])

    return parser
