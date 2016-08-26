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
Properties interface.
"""

class Properties(object):
    """
    Properties interface.
    """

    _INTERFACE_NAME = 'org.freedesktop.DBus.Properties'

    def __init__(self, dbus_object):
        """
        Initializer.

        :param dbus_object: the dbus object
        """
        self._dbus_object = dbus_object

    def Get(self, interface_name, property_name):
        """
        Get a property.

        :param str interface_name: the interface that supplies this prop
        :param str property_name: a property name
        :returns: the property
        :rtype: Variant
        """
        return self._dbus_object.Get(
           interface_name,
           property_name,
           dbus_interface=self._INTERFACE_NAME
        )

    def GetAll(self, interface_name):
        """
        Get all properties belonging to ``interface_name``.

        :param str interface_name: the interface name
        :returns: the properties belonging to this interface
        :rtype: Dict of (String * Variant)
        """
        return self._dbus_object.GetAll(
           interface_name,
           dbus_interface=self._INTERFACE_NAME
        )

    def Set(self, interface_name, property_name, value):
        """
        Set a property.

        :param str interface_name: the interface name
        :param str property_name: a property name
        :param object value: the value to set
        """
        self._dbus_object.Set(
           interface_name,
           property_name,
           value,
           dbus_interface=self._INTERFACE_NAME
        )
