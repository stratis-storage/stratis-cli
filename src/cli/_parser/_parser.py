"""
Top level parser for Stratis CLI.
"""


import argparse

from .._actions import PoolActions
from .._actions import MetaActions

from ._lib import device_from_path
from ._logical import build_logical_parser
from ._physical import build_physical_parser


def build_meta_parser(parser):
    """
    Generates the parser appropriate for obtaining information about this
    program.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for obtaining meta-information
    :rtype: ArgumentParser
    """

    parser.add_argument(
       '--stratisd-version',
       action='store_true',
       default=False,
       help='version of stratisd daemon'
    )
    parser.set_defaults(func=MetaActions.list_stratisd_version)
    return parser


def build_list_parser(parser):
    """
    Generate the parser appropriate for displaying information.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for listing pools
    :rtype: ArgumentParser
    """
    parser.set_defaults(func=PoolActions.list_pools)
    return parser


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
       nargs='+',
       type=device_from_path
    )
    parser.add_argument(
       '--force',
       action="store_true",
       default=False,
       help="overwrite all existing data and metadata on selected devices"
    )
    parser.add_argument(
       '--redundancy',
       action='store',
       choices=['none'],
       default='none',
       help="redundancy selection for this pool"
    )
    parser.set_defaults(func=PoolActions.create_pool)
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
    parser.add_argument(
       '--force',
       action="store_true",
       default=False,
       help="disregard the presence of any data or metadata"
    )
    parser.set_defaults(func=PoolActions.destroy_pool)
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
    return parser


_SUBPARSER_TABLE = {
   'create' : build_create_parser,
   'destroy' : build_destroy_parser,
   'list' : build_list_parser,
   'logical' : build_logical_parser,
   'meta' : build_meta_parser,
   'physical' : build_physical_parser,
   'rename' : build_rename_parser
}


def gen_parser():
    """
    Make the parser.

    :returns: a fully constructed parser for command-line arguments
    :rtype: ArgumentParser
    """
    parser = argparse.ArgumentParser(description="Stratis Storage Manager")

    subparsers = \
       parser.add_subparsers(dest='subparser_name', title='subcommands')

    subparser_table = dict()

    subparser_table['create'] = \
       subparsers.add_parser('create', description="Create New Stratis Pool")
    _SUBPARSER_TABLE['create'](subparser_table['create'])

    subparser_table['destroy'] = \
       subparsers.add_parser(
          'destroy',
          description="Destroy Existing Stratis Pool"
    )
    _SUBPARSER_TABLE['destroy'](subparser_table['destroy'])

    subparser_table['list'] = \
       subparsers.add_parser('list', description="List Stratis Pools")
    _SUBPARSER_TABLE['list'](subparser_table['list'])

    subparser_table['logical'] = \
       subparsers.add_parser(
          'logical',
          description="Administer Logical Aspects of Specified Pool"
       )
    _SUBPARSER_TABLE['logical'](subparser_table['logical'])

    subparser_table['meta'] = \
       subparsers.add_parser('meta', description="Information about Stratis")
    _SUBPARSER_TABLE['meta'](subparser_table['meta'])

    subparser_table['physical'] = \
       subparsers.add_parser(
          'physical',
          description="Administer Physical Aspects of Specified Pool"
       )
    _SUBPARSER_TABLE['physical'](subparser_table['physical'])

    subparser_table['rename'] = \
       subparsers.add_parser('rename', description="Rename a Pool")
    _SUBPARSER_TABLE['rename'](subparser_table['rename'])

    return parser
