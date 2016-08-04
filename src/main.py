import dbus

from cli import gen_parser

def main():
    parser = gen_parser()
    args = parser.parse_args()
    print(args)
    session_bus = dbus.SessionBus()
    proxy = session_bus.get_object(
       'org.storage.stratis1',
       '/org/storage/stratis1'
    )
    interface = dbus.Interface(
       proxy,
       dbus_interface='org.storage.stratis1.Manager'
    )
    args.func(interface, args)

if __name__ == "__main__":
    main()
