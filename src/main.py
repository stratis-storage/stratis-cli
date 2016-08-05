import dbus

from cli import gen_parser
from cli import SERVICE
from cli import TOP_OBJECT
from cli import MANAGER_INTERFACE

def main():
    parser = gen_parser()
    args = parser.parse_args()
    print(args)
    session_bus = dbus.SessionBus()
    proxy = session_bus.get_object(SERVICE, TOP_OBJECT)
    interface = dbus.Interface(proxy, dbus_interface=MANAGER_INTERFACE)
    (rc, message) = args.func(interface, args)
    print(message)
    return rc

if __name__ == "__main__":
    main()
