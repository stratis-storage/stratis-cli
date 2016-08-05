import os

from cli import gen_parser

def main():
    parser = gen_parser()
    args = parser.parse_args()
    print(args)
    print(os.linesep)
    (rc, message) = args.func(args)
    print(message)
    return rc

if __name__ == "__main__":
    main()
