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

from justbytes import Range

from .._errors import StratisCliEngineError
from .._stratisd_constants import StratisdErrors

from ._connection import get_object
from ._constants import SECTOR_SIZE
from ._constants import TOP_OBJECT
from ._constants import UNKNOWN_VALUE_MARKER
from ._data import devs
from ._data import MODev
from ._data import MOPool
from ._data import ObjectManager
from ._data import Pool
from ._data import pools
from ._data import unique
from ._formatting import print_table


def state_val_to_string(val):
    """
    Convert a blockdev state enumerated value to a string.
    """
    states = ["Missing", "Bad", "Spare", "Not-in-use", "In-use"]
    try:
        return states[val]
    except IndexError:
        return UNKNOWN_VALUE_MARKER


def tier_val_to_string(val):
    """
    Convert a blockdev tier enumerated value to a string.
    """
    states = ["Data", "Cache"]
    try:
        return states[val]
    except IndexError:
        return UNKNOWN_VALUE_MARKER


class PhysicalActions():
    """
    Actions on the physical aspects of a pool.
    """

    @staticmethod
    def list_pool(namespace):
        """
        List devices. If a pool is specified in the namespace, list devices
        for that pool. Otherwise, list all devices for all pools.
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        if getattr(namespace, "pool_name", None) is not None:
            (parent_pool_object_path, _) = unique(
                pools(props={
                    'Name': namespace.pool_name
                }).search(managed_objects))

            properties = {"Pool": parent_pool_object_path}
            path_to_name = {parent_pool_object_path: namespace.pool_name}
        else:
            properties = {}
            path_to_name = dict(
                (path, MOPool(info).Name())
                for path, info in pools().search(managed_objects))

        modevs = [
            MODev(info)
            for _, info in devs(props=properties, ).search(managed_objects)
        ]
        tables = [[
            path_to_name[modev.Pool()],
            modev.Devnode(),
            str(Range(modev.TotalPhysicalSize(), SECTOR_SIZE)),
            state_val_to_string(modev.State()),
            tier_val_to_string(modev.Tier())
        ] for modev in modevs]
        print_table(
            ["Pool Name", "Device Node", "Physical Size", "State", "Tier"],
            sorted(tables, key=lambda entry: (entry[0], entry[1])),
            ['<', '<', '>', '>', '>'])

    @staticmethod
    def add_data_device(namespace):
        """
        Add a device to a pool.
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = unique(
            pools(props={
                'Name': namespace.pool_name
            }).search(managed_objects))

        (_, rc, message) = Pool.Methods.AddDataDevs(
            get_object(pool_object_path), {
                'force': namespace.force,
                'devices': namespace.device
            })
        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)

    @staticmethod
    def add_cache_device(namespace):
        """
        Add a device to a pool.
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = unique(
            pools(props={
                'Name': namespace.pool_name
            }).search(managed_objects))

        (_, rc, message) = Pool.Methods.AddCacheDevs(
            get_object(pool_object_path), {
                'force': namespace.force,
                'devices': namespace.device
            })
        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)
