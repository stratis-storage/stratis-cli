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
Parser for operations having to with devices in the pool.
"""


from .._actions import PhysicalActions

from ._cache import build_cache_parser


def build_physical_add_parser(parser):
    """
    Generates the parser appropriate for adding devices to a pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for adding devices
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'name',
       action='store',
       help='pool name'
    )
    parser.add_argument(
       'device',
       help='make device D a member of this pool',
       metavar='D',
       nargs='+'
    )
    parser.add_argument(
       '--force',
       action='store_true',
       default=False,
       help="overwrite existing metadata on specified devices"
    )
    parser.set_defaults(func=PhysicalActions.add_device)
    return parser


def build_physical_list_parser(parser):
    """
    Generates the parser appropriate for listing information about physical
    aspects of a pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for listing physical information about a pool
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'name',
       action='store',
       help='pool name'
    )
    parser.set_defaults(func=PhysicalActions.list_pool)
    return parser


_SUBPARSER_TABLE = {
   'add' : build_physical_add_parser,
   'cache' : build_cache_parser,
   'list' : build_physical_list_parser
}


def build_physical_parser(parser):
    """
    Generates the parser appropriate for administering physical aspects of
    a specified pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for administering physical aspects of a pool
    :rtype: ArgumentParser
    """

    subparsers = \
       parser.add_subparsers(dest='subparser_name', title='subcommands')

    subparser_table = dict()

    subparser_table['add'] = \
       subparsers.add_parser(
          'add',
          description="Add Devices to a Pool"
       )
    _SUBPARSER_TABLE['add'](subparser_table['add'])

    subparser_table['cache'] = \
       subparsers.add_parser(
          'cache',
          description="Cache Commands for this Pool"
       )
    _SUBPARSER_TABLE['cache'](subparser_table['cache'])

    subparser_table['list'] = \
       subparsers.add_parser(
          'list',
          description="List Pool Information"
       )
    _SUBPARSER_TABLE['list'](subparser_table['list'])

    return parser
