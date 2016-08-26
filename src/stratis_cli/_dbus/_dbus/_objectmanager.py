"""
ObjectManager interface.
"""

from ..._errors import StratisCliKnownBugError

class ObjectManager(object):
    """
    ObjectManager interface.
    """
    # pylint: disable=too-few-public-methods
    # pylint: disable=no-self-use

    _INTERFACE_NAME = 'org.freedesktop.DBus.ObjectManager'

    def __init__(self, dbus_object):
        """
        Initializer.

        :param dbus_object: the dbus object
        """
        self._dbus_object = dbus_object

    def GetManagedObjects(self):
        """
        Get the managed objects.

        :rtype: Dict
        """
        raise StratisCliKnownBugError(
           "This has never been observed to return anything but {}."
        )
