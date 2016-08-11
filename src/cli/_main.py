"""
Highest level runner.
"""
from ._parser import gen_parser

def run(command_line_args):
    """
    Run according to the arguments passed.
    """
    parser = gen_parser()
    args = parser.parse_args(command_line_args)
    yield args
    (rc, message) = args.func(args)
    yield (rc, message)
