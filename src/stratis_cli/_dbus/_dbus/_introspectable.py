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
