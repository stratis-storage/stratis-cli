import dbus

from cli import gen_parser

def main():
    parser = gen_parser()
    args = parser.parse_args()
    print(args)
    session_bus = dbus.SessionBus()

if __name__ == "__main__":
    main()
