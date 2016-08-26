"""
Peer interface.
"""

class Peer(object):
    """
    Peer interface.
    """

    _INTERFACE_NAME = 'org.freedesktop.DBus.Peer'

    def __init__(self, dbus_object):
        """
        Initializer.

        :param dbus_object: the dbus object
        """
        self._dbus_object = dbus_object

    def GetMachineId(self):
        """
        Get the machine id.

        :rtype: String
        """
        return self._dbus_object.GetMachineId(self._INTERFACE_NAME)

    def Ping(self):
        """
        Ping.
        """
        self._dbus_object.Ping(self._INTERFACE_NAME)
