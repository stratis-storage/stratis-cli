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
