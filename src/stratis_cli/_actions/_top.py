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
Miscellaneous top-level actions.
"""

from justbytes import Range

from .._errors import StratisCliEngineError

from .._stratisd_constants import StratisdErrors

from ._connection import get_object
from ._constants import TOP_OBJECT
from ._constants import SECTOR_SIZE
from ._data import Manager
from ._data import MOPool
from ._data import ObjectManager
from ._data import Pool
from ._data import pools
from ._data import unique
from ._formatting import print_table


class TopActions():
    """
    Top level actions.
    """

    @staticmethod
    def create_pool(namespace):
        """
        Create a stratis pool.

        :raises StratisCliEngineError:
        """
        proxy = get_object(TOP_OBJECT)

        (_, rc, message) = Manager.Methods.CreatePool(
            proxy, {
                'name': namespace.pool_name,
                'redundancy': (True, 0),
                'devices': namespace.blockdevs
            })

        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)

    @staticmethod
    def list_pools(_):
        """
        List all stratis pools.

        :raises StratisCliEngineError:
        """
        proxy = get_object(TOP_OBJECT)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        mopools = (MOPool(info) for _, info in pools().search(managed_objects))
        tables = [[
            mopool.Name(),
            str(Range(mopool.TotalPhysicalSize(), SECTOR_SIZE)),
            str(Range(mopool.TotalPhysicalUsed(), SECTOR_SIZE)),
        ] for mopool in mopools]
        print_table(['Name', 'Total Physical Size', 'Total Physical Used'],
                    sorted(tables, key=lambda entry: entry[0]),
                    ['<', '>', '>'])

    @staticmethod
    def destroy_pool(namespace):
        """
        Destroy a stratis pool.

        If no pool exists, the method succeeds.

        :raises StratisCliEngineError:
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = unique(
            pools(props={
                'Name': namespace.pool_name
            }).search(managed_objects))

        (_, rc, message) = \
           Manager.Methods.DestroyPool(proxy, {'pool': pool_object_path})

        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)

    @staticmethod
    def rename_pool(namespace):
        """
        Rename a pool.
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = unique(
            pools(props={
                'Name': namespace.current
            }).search(managed_objects))

        (_, rc, message) = Pool.Methods.SetName(
            get_object(pool_object_path), {'name': namespace.new})

        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)

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
            get_object(pool_object_path), {'devices': namespace.device})
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
            get_object(pool_object_path), {'devices': namespace.device})
        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)
