"""
Class for wrapping dbus calls.
"""

from ._dbus import Properties

from .._errors import StratisCliUnimplementedError


class Pool(object):
    """
    Class that implements stratis pool interface.
    """

    _INTERFACE_NAME = 'org.storage.stratis1.pool'

    def __init__(self, dbus_object):
        """
        Initializer.

        :param dbus_object: the dbus object that implements a pool
        """
        self._dbus_object = dbus_object

    def AddCache(self, devices):
        """
        Add a cache constructed from ``devices`` to the pool.
        """
        return self._dbus_object.AddCache(
           devices,
           dbus_interface=self._INTERFACE_NAME
        )

    def CreateVolumes(self, volumes):
        """
        Create volumes from the pool.
        """
        return self._dbus_object.CreateVolumes(
           volumes,
           dbus_interface=self._INTERFACE_NAME
        )

    def DestroyVolume(self):
        """
        Destroy a volume.
        """
        raise StratisCliUnimplementedError()

    def ListCache(self):
        """
        List information about the pool's cache.
        """
        return self._dbus_object.ListCache(
           dbus_interface=self._INTERFACE_NAME
        )

    def ListDevs(self):
        """
        List the devices belonging to a pool.
        """
        return self._dbus_object.ListDevs(dbus_interface=self._INTERFACE_NAME)

    def ListVolumes(self):
        """
        List the volumes belonging to a pool.
        """
        return self._dbus_object.ListVolumes(
           dbus_interface=self._INTERFACE_NAME
        )

    def RemoveCache(self):
        """
        Remove a cache from a pool.
        """
        raise StratisCliUnimplementedError()

    @property
    def SPool(self):
        """
        Name of the pool.

        :rtype: String
        """
        return Properties(self._dbus_object).Get(
           self._INTERFACE_NAME,
           'SPool'
        )
