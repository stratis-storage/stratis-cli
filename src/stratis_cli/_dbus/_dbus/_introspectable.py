"""
Introspectable interface.
"""

class Introspectable(object):
    """
    Introspectable interface.
    """
    # pylint: disable=too-few-public-methods

    _INTERFACE_NAME = 'org.freedesktop.DBus.Introspectable'

    def __init__(self, dbus_object):
        """
        Initializer.

        :param dbus_object: the dbus object
        """
        self._dbus_object = dbus_object

    def Introspect(self):
        """
        Introspect on the interfaces of this object.

        :returns: introspection information
        :rtype: String (of XML)
        """
        return self._dbus_object.Introspect(dbus_interface=self._INTERFACE_NAME)
