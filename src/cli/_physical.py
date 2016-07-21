import argparse

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
    return parser


def build_physical_remove_parser(parser):
    """
    Generates the parser appropriate for removing physical devices from a pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for removing physical devices from a pool
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'name',
       action='store',
       help='pool name'
    )
    parser.add_argument(
       'device',
       help='remove device D from this pool',
       metavar='D',
       nargs='+'
    )
    return parser


def build_physical_parser(parser):
    """
    Generates the parser appropriate for administering physical aspects of
    a specified pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for administering physical aspects of a pool
    :rtype: ArgumentParser
    """

    subparsers = parser.add_subparsers(title='subcommands')

    subparser_table = dict()

    subparser_table['add'] = \
       subparsers.add_parser(
          'add',
          description="Add Devices to a Pool"
       )
    build_physical_add_parser(subparser_table['add'])

    subparser_table['cache'] = \
       subparsers.add_parser(
          'cache',
          description="Cache Commands for this Pool"
       )
    build_cache_parser(subparser_table['cache'])

    subparser_table['list'] = \
       subparsers.add_parser(
          'list',
          description="List Pool Information"
       )
    build_physical_list_parser(subparser_table['list'])

    subparser_table['remove'] = \
       subparsers.add_parser(
          'remove',
          description="Remove Devices from a Pool"
       )
    build_physical_remove_parser(subparser_table['remove'])

    return parser
