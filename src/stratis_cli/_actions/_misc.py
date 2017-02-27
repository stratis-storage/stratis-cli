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
Miscellaneous shared methods.
"""

from stratisd_client_dbus import get_managed_objects

from .._errors import StratisCliValueError


class GetObjectPath(object):
    """
    Implements getting the DBus object path for various stratisd entities.

    Raises a StratisCliValueError if no object path for specification.
    """

    @staticmethod
    def _get_object_path(top, name, spec=None):
        things = getattr(get_managed_objects(top), name)(spec)
        next_thing = next(things, None)
        if next_thing is None:
            raise StratisCliValueError(spec, "spec")

        return next_thing[0]

    @staticmethod
    def get_pool(top, spec=None):
        """
        Get pool.

        :param top: the top object
        :param spec: what properties to use to locate the pool
        :returns: an appropriate pool object path
        :rtype: str
        :raises StratisCliValueError: if failure to get object path for spec
        """
        return GetObjectPath._get_object_path(top, 'pools', spec)

    @staticmethod
    def get_filesystem(top, spec=None):
        """
        Get filesystem.

        :param top: the top object
        :param spec: what properties to use to locate the filesystem
        :returns: an appropriate filesystem object path
        :rtype: str
        :raises StratisCliValueError: if failure to get object path for spec
        """
        return GetObjectPath._get_object_path(top, 'filesystems', spec)
