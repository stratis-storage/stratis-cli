import argparse


def build_list_parser(parser):
    """
    Generate the parser appropriate for displaying information.

    :param ArgumentParser parser: a parser
    :returns: a completed parser for listing pools
    :rtype: ArgumentParser
    """
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
       nargs='+'
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
       choices=['single'],
       default='single',
       help="redundancy selection for this pool"
    )
    return parser


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


def gen_parser():
    """
    Make the parser.

    :returns: a fully constructed parser for command-line arguments
    :rtype: ArgumentParser
    """
    parser = argparse.ArgumentParser(description="Stratis Storage Manager")

    subparsers = parser.add_subparsers(title="subcommands")

    subparser_names = ('cache', 'create', 'dev', 'list', 'vol')

    subparser_table = dict()

    subparser_table['list'] = \
       subparsers.add_parser('list', description="List Stratis Pools")
    build_list_parser(subparser_table['list'])

    subparser_table['create'] = \
       subparsers.add_parser('create', description="Create New Stratis Pool")
    build_create_parser(subparser_table['create'])

    subparser_table['physical'] = \
       subparsers.add_parser(
          'physical',
          description="Administer Physical Aspects of Specified Pool"
       )
    build_physical_parser(subparser_table['physical'])

    subparser_table['logical'] = \
       subparsers.add_parser(
          'logical',
          description="Administer Logical Aspects of Specified Pool"
       )

    return parser
