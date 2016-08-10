"""
Parser for logical aspects of CLI.
"""

from .._actions import LogicalActions


def build_logical_create_parser(parser):
    """
    Generates the parser appropriate for creating volumes from a pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for creating volumes from a pool
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'pool',
       action='store',
       help='pool name'
    )
    parser.add_argument(
       'volume',
       help='create a volume V from this pool',
       metavar='V',
       nargs='+'
    )
    parser.set_defaults(func=LogicalActions.create_volumes)
    return parser


def build_logical_list_parser(parser):
    """
    Generates the parser appropriate for listing information about logical
    aspects of a pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for listing logical information about a pool
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'pool',
       action='store',
       help='pool name'
    )
    parser.set_defaults(func=LogicalActions.list_volumes)
    return parser


def build_logical_destroy_parser(parser):
    """
    Generates the parser appropriate for removing logical volumes from a pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for removing logical volumes from a pool
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'name',
       action='store',
       help='pool name'
    )
    parser.add_argument(
       'volume',
       help='remove volume V from this pool',
       metavar='V',
       nargs='+'
    )
    return parser


def build_logical_snapshot_parser(parser):
    """
    Generates the parser appropriate for taking snapshots of existing logical
    volumes.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for specifying snapshots
    :rtype: ArgumentParser
    """
    parser.add_argument(
       'name',
       action='store',
       help='pool name'
    )
    parser.add_argument(
       'origin',
       action='store',
       help='origin volume',
    )
    parser.add_argument(
       'volume',
       help='snapshot volume S of origin',
       metavar='S',
       nargs='+'
    )
    return parser


_SUBPARSER_TABLE = {
   'create' : build_logical_create_parser,
   'destroy' : build_logical_destroy_parser,
   'list' : build_logical_list_parser,
   'snapshot' : build_logical_snapshot_parser,
}


def build_logical_parser(parser):
    """
    Generates the parser appropriate for administering logical aspects of
    a specified pool.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for administering logical aspects of a pool
    :rtype: ArgumentParser
    """

    subparsers = \
       parser.add_subparsers(dest='subparser_name', title='subcommands')

    subparser_table = dict()

    subparser_table['create'] = \
       subparsers.add_parser(
          'create',
          description="Create a Logical Volume from an Existing Pool"
       )
    _SUBPARSER_TABLE['create'](subparser_table['create'])

    subparser_table['list'] = \
       subparsers.add_parser(
          'list',
          description="List Information about Logical Volumes in Pool"
       )
    _SUBPARSER_TABLE['list'](subparser_table['list'])

    subparser_table['destroy'] = \
       subparsers.add_parser(
          'destroy',
          description="Destroy Volumes Belonging to a Pool"
       )
    _SUBPARSER_TABLE['destroy'](subparser_table['destroy'])

    subparser_table['snapshot'] = \
       subparsers.add_parser(
          'snapshot',
          description="Create a Snapshot of an Existing Logical Volume"
       )
    _SUBPARSER_TABLE['snapshot'](subparser_table['snapshot'])

    return parser
