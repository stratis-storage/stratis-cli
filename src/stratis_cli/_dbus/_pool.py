# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

    def AddDevs(self, devices):
        """
        Add devices to the pool.
        """
        return self._dbus_object.AddDevs(
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

    def DestroyVolumes(self, volumes):
        """
        Destroy volumes in the pool.

        :param volumes: list of volume names
        :type volumes: list of str
        """
        return self._dbus_object.DestroyVolumes(
           volumes,
           dbus_interface=self._INTERFACE_NAME
        )

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
        # pylint: disable=no-self-use
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
