"""
Highest level runner.
"""

import sys

import dbus

from ._constants import SERVICE
from ._constants import SERVICE_UNKNOWN_ERROR

from ._parser import gen_parser

def run(command_line_args):
    """
    Run according to the arguments passed.
    """
    parser = gen_parser()
    args = parser.parse_args(command_line_args)
    yield args
    try:
        (rc, message) = args.func(args)
    except dbus.exceptions.DBusException as err:
        message = str(err)
        if message.startswith(SERVICE_UNKNOWN_ERROR):
            sys.exit('stratisd dbus service %s not started' % SERVICE)
        raise err
    yield (rc, message)
