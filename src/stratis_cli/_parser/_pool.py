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
Parser for top-level pool actions of CLI.
"""

from .._actions import TopActions


def build_create_parser(parser):
    """
    Generates the parser appropriate for creating a pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for creating a pool
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'name',
       action='store',
       help='name to assign to pool'
    )
    parser.add_argument(
       'device',
       help='make device D a member of this pool',
       metavar='D',
       nargs='+'
    )
    parser.add_argument(
       '--redundancy',
       action='store',
       choices=['none'],
       default='none',
       help="redundancy selection for this pool"
    )
    parser.set_defaults(func=TopActions.create_pool)
    return parser


def build_destroy_parser(parser):
    """
    Generates the parser appropriate for destroying a pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for destroying a pool
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'name',
       action='store',
       help='name of pool'
    )
    parser.set_defaults(func=TopActions.destroy_pool)
    return parser


def build_list_parser(parser):
    """
    Generate the parser appropriate for displaying information.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for listing pools
    :rtype: ArgumentParser
    """
    parser.set_defaults(func=TopActions.list_pools)
    return parser


def build_rename_parser(parser):
    """
    Generates the parser appropriate for renaming a pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for renaming a pool
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'current',
       action='store',
       help='current name of pool'
    )
    parser.add_argument('new', action='store', help='desired name')
    parser.set_defaults(func=TopActions.rename_pool)
    return parser


_SUBPARSER_TABLE = {
   'create' : build_create_parser,
   'destroy' : build_destroy_parser,
   'list' : build_list_parser,
   'rename' : build_rename_parser
}


def build_pool_parser(parser):
    """
    Generates the parser appropriate for top-level pool actions.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for top-level pool actions
    :rtype: ArgumentParser
    """

    subparsers = \
       parser.add_subparsers(dest='subparser_name', title='subcommands')

    subparser_table = dict()

    subparser_table['create'] = \
       subparsers.add_parser('create', description="Create a Pool")
    _SUBPARSER_TABLE['create'](subparser_table['create'])

    subparser_table['destroy'] = \
       subparsers.add_parser('destroy', description="Destroy a Pool")
    _SUBPARSER_TABLE['destroy'](subparser_table['destroy'])

    subparser_table['list'] = \
       subparsers.add_parser(
          'list',
          description="List Information about Pools"
       )
    _SUBPARSER_TABLE['list'](subparser_table['list'])

    subparser_table['rename'] = \
       subparsers.add_parser('rename', description="Rename a Pool")
    _SUBPARSER_TABLE['rename'](subparser_table['rename'])

    return parser
