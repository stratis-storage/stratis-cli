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
Actions on a pool's cache.
"""

from __future__ import print_function

from .._errors import StratisCliUnimplementedError


class CacheActions(object):
    """
    Actions on a pool's cache.
    """

    @staticmethod
    def add_devices(namespace):
        """
        Add devices to a cache.
        """
        # pylint: disable=unused-argument
        raise StratisCliUnimplementedError("No cache operations implemented.")

    @staticmethod
    def list_cache(namespace):
        """
        List information about the cache belonging to a pool.
        """
        # pylint: disable=unused-argument
        raise StratisCliUnimplementedError("No cache operations implemented.")

    @staticmethod
    def remove_device(namespace):
        """
        Remove a device from the given pool.
        """
        # pylint: disable=unused-argument
        raise StratisCliUnimplementedError("No cache operations implemented.")
