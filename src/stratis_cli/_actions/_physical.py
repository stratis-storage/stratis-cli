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
Miscellaneous physical actions.
"""

from __future__ import print_function

from .._errors import StratisCliRuntimeError
from .._errors import StratisCliUnimplementedError
from .._stratisd_constants import StratisdErrors

from ._connection import get_object
from ._constants import TOP_OBJECT
from ._data import ObjectManager
from ._data import Pool
from ._data import pools


class PhysicalActions(object):
    """
    Actions on the physical aspects of a pool.
    """

    @staticmethod
    def list_pool(namespace):
        """
        List devices in a pool.
        """
        # pylint: disable=unused-argument
        raise StratisCliUnimplementedError("No ability to list pools.")

    @staticmethod
    def add_device(namespace):
        """
        Add a device to a pool.
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = pools(
           managed_objects,
           props={'Name': namespace.pool_name},
           unique=True
        )

        (_, rc, message) = Pool.Methods.AddDevs(
           get_object(pool_object_path),
           {'force': namespace.force, 'devices': namespace.device}
        )
        if rc != StratisdErrors.OK:
            raise StratisCliRuntimeError(rc, message)
        return
