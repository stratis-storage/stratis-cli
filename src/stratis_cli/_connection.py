"""
Miscellaneous helpful methods.
"""

import dbus

from ._constants import SERVICE

class Bus(object):
    """
    Our bus.
    """
    # pylint: disable=too-few-public-methods

    _BUS = None

    @staticmethod
    def get_bus():
        """
        Get our bus.
        """
        if Bus._BUS is None:
            Bus._BUS = dbus.SessionBus()

        return Bus._BUS

def get_object(object_path):
    """
    Get an object from an object path.

    :param str object_path: an object path with a valid format
    :returns: the proxy object corresponding to the object path
    :rtype: ProxyObject
    """
    return Bus.get_bus().get_object(SERVICE, object_path)
