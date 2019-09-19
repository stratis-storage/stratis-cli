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
from .._errors import StratisCliInUseError
from .._errors import StratisCliNoChangeError
from .._errors import StratisCliPartialChangeError

from .._stratisd_constants import BlockDevTiers
from .._stratisd_constants import StratisdErrors

from ._connection import get_object
from ._constants import TOP_OBJECT
from ._constants import SECTOR_SIZE
from ._formatting import print_table


class TopActions:
    """
    Top level actions.
    """

    @staticmethod
    def create_pool(namespace):
        """
        Create a stratis pool.

        :raises StratisCliEngineError:
        """
        from ._data import Manager

        proxy = get_object(TOP_OBJECT)

        ((changed, (_, _)), rc, message) = Manager.Methods.CreatePool(
            proxy,
            {
                "name": namespace.pool_name,
                "redundancy": (True, 0),
                "devices": namespace.blockdevs,
            },
        )

        if rc != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(rc, message)

        if not changed:
            resource = namespace.pool_name
            raise StratisCliNoChangeError("create", resource)

    @staticmethod
    def list_pools(_):
        """
        List all stratis pools.

        :raises StratisCliEngineError:
        """
        from ._data import MOPool
        from ._data import ObjectManager
        from ._data import pools

        proxy = get_object(TOP_OBJECT)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        mopools = (MOPool(info) for _, info in pools().search(managed_objects))
        tables = [
            [
                mopool.Name(),
                str(Range(mopool.TotalPhysicalSize(), SECTOR_SIZE)),
                str(Range(mopool.TotalPhysicalUsed(), SECTOR_SIZE)),
            ]
            for mopool in mopools
        ]
        print_table(
            ["Name", "Total Physical Size", "Total Physical Used"],
            sorted(tables, key=lambda entry: entry[0]),
            ["<", ">", ">"],
        )

    @staticmethod
    def destroy_pool(namespace):
        """
        Destroy a stratis pool.

        If no pool exists, the method succeeds.

        :raises StratisCliEngineError:
        """
        from ._data import Manager
        from ._data import ObjectManager
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        ((changed, _), rc, message) = Manager.Methods.DestroyPool(
            proxy, {"pool": pool_object_path}
        )

        # This branch can be covered, since the engine will return an error
        # if the pool can not be destroyed because it has filesystems.
        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)

        if not changed:
            resource = namespace.pool_name
            raise StratisCliNoChangeError("destroy", resource)

    @staticmethod
    def rename_pool(namespace):
        """
        Rename a pool.
        """
        from ._data import ObjectManager
        from ._data import Pool
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": namespace.current})
            .require_unique_match(True)
            .search(managed_objects)
        )

        ((changed, _), rc, message) = Pool.Methods.SetName(
            get_object(pool_object_path), {"name": namespace.new}
        )

        if rc != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(rc, message)

        if not changed:
            resource = namespace.new
            raise StratisCliNoChangeError("rename", resource)

    @staticmethod
    def add_data_devices(namespace):
        """
        Add specified data devices to a pool.
        """
        # pylint: disable=too-many-locals
        from ._data import MODev
        from ._data import ObjectManager
        from ._data import Pool
        from ._data import devs
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        blockdevs = frozenset(namespace.blockdevs)

        cache = frozenset(
            str(MODev(info).Devnode())
            for (_, info) in devs(props={"Tier": BlockDevTiers.Cache}).search(
                managed_objects
            )
        )
        already_cache = blockdevs.intersection(cache)
        if already_cache != frozenset():
            raise StratisCliInUseError(already_cache, BlockDevTiers.Data)

        data = frozenset(
            str(MODev(info).Devnode())
            for (_, info) in devs(props={"Tier": BlockDevTiers.Data}).search(
                managed_objects
            )
        )
        already_data = blockdevs.intersection(data)

        if already_data != frozenset():
            new_data = blockdevs.difference(already_data)
            raise StratisCliPartialChangeError("add-data", new_data, already_data)

        (_, rc, message) = Pool.Methods.AddDataDevs(
            get_object(pool_object_path), {"devices": namespace.blockdevs}
        )
        if rc != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(rc, message)

    @staticmethod
    def add_cache_devices(namespace):
        """
        Add specified cache devices to a pool.
        """
        # pylint: disable=too-many-locals
        from ._data import MODev
        from ._data import ObjectManager
        from ._data import Pool
        from ._data import devs
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        blockdevs = frozenset(namespace.blockdevs)

        data = frozenset(
            str(MODev(info).Devnode())
            for (_, info) in devs(props={"Tier": BlockDevTiers.Data}).search(
                managed_objects
            )
        )
        already_data = blockdevs.intersection(data)

        if already_data != frozenset():
            raise StratisCliInUseError(already_data, BlockDevTiers.Cache)

        cache = frozenset(
            str(MODev(info).Devnode())
            for (_, info) in devs(props={"Tier": BlockDevTiers.Cache}).search(
                managed_objects
            )
        )
        already_cache = blockdevs.intersection(cache)

        if already_cache != frozenset():
            new_cache = blockdevs.difference(already_cache)
            raise StratisCliPartialChangeError("add-cache", new_cache, already_cache)

        (_, rc, message) = Pool.Methods.AddCacheDevs(
            get_object(pool_object_path), {"devices": namespace.blockdevs}
        )
        if rc != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(rc, message)
