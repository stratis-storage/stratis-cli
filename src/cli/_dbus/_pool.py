"""
Class for wrapping dbus calls.
"""

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

    def AddCache(self):
        """
        Add a cache to the pool.
        """
        raise StratisCliUnimplementedError()

    def CreateVolume(self):
        """
        Create a volume from the pool.
        """
        raise StratisCliUnimplementedError()

    def DestroyVolume(self):
        """
        Destroy a volume.
        """
        raise StratisCliUnimplementedError()

    def ListDevs(self):
        """
        List the devices belonging to a pool.
        """
        return self._dbus_object.ListDevs(dbus_interface=self._INTERFACE_NAME)

    def ListVolumes(self):
        """
        List the volumes belonging to a pool.
        """
        raise StratisCliUnimplementedError()

    def RemoveCache(self):
        """
        Remove a cache from a pool.
        """
        raise StratisCliUnimplementedError()
