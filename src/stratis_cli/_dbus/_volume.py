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


class Volume(object):
    """
    Class that implements stratis volume interface.
    """
    # pylint: disable=too-few-public-methods

    _INTERFACE_NAME = 'org.storage.stratis1.volume'

    def __init__(self, dbus_object):
        """
        Initializer.

        :param dbus_object: the dbus object that implements a pool
        """
        self._dbus_object = dbus_object

    def CreateSnapshot(self, name):
        """
        Create a snapshot of this volume with name ``name``.

        :param str name: name of snapshot volume
        """
        return self._dbus_object.CreateSnapshot(
           name,
           dbus_interface=self._INTERFACE_NAME
        )
