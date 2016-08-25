"""
Parser for cache operations.
"""


from .._actions import CacheActions


def build_cache_add_parser(parser):
    """
    Generates the parser appropriate for adding devices to a pool cache.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for adding devices to a pool cache
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'pool',
       action='store',
       help='pool name'
    )
    parser.add_argument(
       'device',
       help='add device D to this pool\'s cache',
       metavar='D',
       nargs='+'
    )
    parser.set_defaults(func=CacheActions.add_devices)
    return parser


def build_cache_create_parser(parser):
    """
    Generates the parser appropriate for creating a cache for this pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for creating a cache for this pool.
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'pool',
       action='store',
       help='pool name'
    )
    parser.add_argument(
       'device',
       help='make device D a member of this pool\'s cache',
       metavar='D',
       nargs='+'
    )
    parser.add_argument(
       '--redundancy',
       choices=['none'],
       default='none',
       help='redundancy for cache'
    )
    parser.set_defaults(func=CacheActions.create_cache)
    return parser


def build_cache_list_parser(parser):
    """
    Generates the parser appropriate for listing information about cache
    aspects of a pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for listing cache information about a pool
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'pool',
       action='store',
       help='pool name'
    )
    parser.set_defaults(func=CacheActions.list_cache)
    return parser


def build_cache_remove_parser(parser):
    """
    Generates the parser appropriate for removing cache devices from a pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for removing cache devices from a pool
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'pool',
       action='store',
       help='pool name'
    )
    parser.add_argument(
       'device',
       help="remove device D from this pool's cache",
       metavar='D',
       nargs='+'
    )
    parser.set_defaults(func=CacheActions.remove_device)
    return parser


_SUBPARSER_TABLE = {
   'add' : build_cache_add_parser,
   'create' : build_cache_create_parser,
   'list' : build_cache_list_parser,
   'remove' : build_cache_remove_parser
}


def build_cache_parser(parser):
    """
    Generates the parser appropriate for administering cache aspects of
    a specified pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for administering cache aspects of a pool
    :rtype: ArgumentParser
    """

    subparsers = \
       parser.add_subparsers(dest='subparser_name', title='subcommands')

    subparser_table = dict()

    subparser_table['add'] = \
       subparsers.add_parser(
          'add',
          description="Add Devices to an Existing Pool Cache"
       )
    _SUBPARSER_TABLE['add'](subparser_table['add'])

    subparser_table['create'] = \
       subparsers.add_parser(
          'create',
          description="Create a Cache for an Existing Pool"
       )
    _SUBPARSER_TABLE['create'](subparser_table['create'])

    subparser_table['list'] = \
       subparsers.add_parser(
          'list',
          description="List Information about Cache Devices in Pool"
       )
    _SUBPARSER_TABLE['list'](subparser_table['list'])

    subparser_table['remove'] = \
       subparsers.add_parser(
          'remove',
          description="Remove Cache Device from a Pool Cache"
       )
    _SUBPARSER_TABLE['remove'](subparser_table['remove'])

    return parser
