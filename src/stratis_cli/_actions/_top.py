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

# isort: THIRDPARTY
from justbytes import Range

from .._errors import (
    StratisCliEngineError,
    StratisCliIncoherenceError,
    StratisCliInUseOtherTierError,
    StratisCliInUseSameTierError,
    StratisCliNameConflictError,
    StratisCliNoChangeError,
    StratisCliPartialChangeError,
)
from .._stratisd_constants import BlockDevTiers, StratisdErrors
from ._connection import get_object
from ._constants import POOL_INTERFACE, TOP_OBJECT
from ._formatting import TABLE_FAILURE_STRING, fetch_property, print_table


def _generate_pools_to_blockdevs(managed_objects, to_be_added, tier):
    """
    Generate a map of pools to which block devices they own
    :param managed_objects: the result of a GetManagedObjects call
    :type managed_objects: dict of str * dict
    :returns: a map of pool names to sets of strings containing blockdevs they own
    :rtype: dict of str * frozenset of str
    """
    # pylint: disable=import-outside-toplevel
    from ._data import MODev
    from ._data import MOPool
    from ._data import devs
    from ._data import pools

    pool_map = dict(
        (path, MOPool(info).Name()) for (path, info) in pools().search(managed_objects)
    )

    pools_to_blockdevs = {}
    for (_, info) in devs(props={"Tier": tier}).search(managed_objects):
        modev = MODev(info)
        if modev.Devnode() in to_be_added:
            pool_name = pool_map[modev.Pool()]
            if pool_name not in pools_to_blockdevs:
                pools_to_blockdevs[pool_name] = []
            pools_to_blockdevs[pool_name].append(str(modev.Devnode()))

    return dict(
        (pool, frozenset(blockdevs)) for pool, blockdevs in pools_to_blockdevs.items()
    )


def _check_opposite_tier(managed_objects, to_be_added, other_tier):
    """
    Check whether specified blockdevs are already in the other tier.

    :param managed_objects: the result of a GetManagedObjects call
    :type managed_objects: dict of str * dict
    :param to_be_added: the blockdevs to be added
    :type to_be_added: frozenset of str
    :param other_tier: the other tier, not the one requested
    :type other_tier: _stratisd_constants.BlockDevTiers
    :raises StratisCliInUseOtherTierError: if blockdevs are used by other tier
    """
    # pylint: disable=import-outside-toplevel
    from ._data import MODev
    from ._data import MOPool
    from ._data import devs
    from ._data import pools

    pools_to_blockdevs = _generate_pools_to_blockdevs(
        managed_objects, to_be_added, other_tier
    )

    if pools_to_blockdevs != {}:
        raise StratisCliInUseOtherTierError(
            pools_to_blockdevs,
            BlockDevTiers.Data
            if other_tier == BlockDevTiers.Cache
            else BlockDevTiers.Cache,
        )


def _check_same_tier(pool_name, managed_objects, to_be_added, this_tier):
    """
    Check whether specified blockdevs are already in the tier to which they
    are to be added.

    :param managed_objects: the result of a GetManagedObjects call
    :type managed_objects: dict of str * dict
    :param to_be_added: the blockdevs to be added
    :type to_be_added: frozenset of str
    :param other_tier: the tier requested
    :type other_tier: _stratisd_constants.BlockDevTiers
    :raises StratisCliPartialChangeError: if blockdevs are used by this tier
    :raises StratisCliInUseSameTierError: if blockdevs are used by this tier in another pool
    """
    # pylint: disable=import-outside-toplevel
    from ._data import MODev
    from ._data import devs

    pools_to_blockdevs = _generate_pools_to_blockdevs(
        managed_objects, to_be_added, this_tier
    )

    owned_by_current_pool = frozenset(
        devnode
        for pool, devnodes in pools_to_blockdevs.items()
        for devnode in devnodes
        if pool_name == pool
    )
    owned_by_other_pools = dict(
        (pool, devnodes)
        for pool, devnodes in pools_to_blockdevs.items()
        if pool_name != pool
    )

    if owned_by_current_pool != frozenset():
        raise StratisCliPartialChangeError(
            "add to cache" if this_tier == BlockDevTiers.Cache else "add to data",
            to_be_added.difference(owned_by_current_pool),
            to_be_added.intersection(owned_by_current_pool),
        )
    if owned_by_other_pools != {}:
        raise StratisCliInUseSameTierError(owned_by_other_pools, this_tier)


class TopActions:
    """
    Top level actions.
    """

    @staticmethod
    def create_pool(namespace):
        """
        Create a stratis pool.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        :raises StratisCliNameConflictError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import Manager
        from ._data import ObjectManager
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        names = pools(props={"Name": namespace.pool_name}).search(managed_objects)
        if list(names) != []:
            raise StratisCliNameConflictError("pool", namespace.pool_name)

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

        if not changed:  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    "Expected to create the specified pool %s but stratisd "
                    "reports that it did not actually create the pool"
                )
                % namespace.pool_name
            )

    @staticmethod
    def list_pools(_):
        """
        List all stratis pools.

        :raises StratisCliEngineError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import FetchProperties
        from ._data import MOPool
        from ._data import ObjectManager
        from ._data import pools

        proxy = get_object(TOP_OBJECT)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        pools_with_props = [
            (
                FetchProperties.Methods.GetAllProperties(get_object(objpath), {}),
                MOPool(info),
            )
            for objpath, info in pools().search(managed_objects)
        ]

        def physical_size_triple(props):
            """
            Calculate the triple to display for total physical size.

            The format is total/used/free where the display value for each
            member of the tuple are chosen automatically according to justbytes'
            configuration.

            :param props: a dictionary of property values obtained
            :type props: dict of str * object
            :returns: a string to display in the resulting list output
            :rtype: str
            """
            total_physical_size = fetch_property(
                POOL_INTERFACE, props, "TotalPhysicalSize", Range
            )
            total_physical_used = fetch_property(
                POOL_INTERFACE, props, "TotalPhysicalUsed", Range
            )

            total_physical_free = (
                None
                if total_physical_size is None or total_physical_used is None
                else total_physical_size - total_physical_used
            )

            return "%s / %s / %s" % (
                TABLE_FAILURE_STRING
                if total_physical_size is None
                else total_physical_size,
                TABLE_FAILURE_STRING
                if total_physical_used is None
                else total_physical_used,
                TABLE_FAILURE_STRING
                if total_physical_free is None
                else total_physical_free,
            )

        tables = [
            (mopool.Name(), physical_size_triple(props))
            for props, mopool in pools_with_props
        ]

        print_table(
            ["Name", "Total Physical"],
            sorted(tables, key=lambda entry: entry[0]),
            ["<", ">"],
        )

    @staticmethod
    def destroy_pool(namespace):
        """
        Destroy a stratis pool.

        If no pool exists, the method succeeds.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        """
        # pylint: disable=import-outside-toplevel
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

        if not changed:  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    "Expected to destroy the specified pool %s but "
                    "stratisd reports that it did not actually "
                    "destroy the pool requested"
                )
                % namespace.pool_name
            )

    @staticmethod
    def rename_pool(namespace):
        """
        Rename a pool.

        :raises StratisCliEngineError:
        :raises StratisCliNoChangeError:
        """
        # pylint: disable=import-outside-toplevel
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
            raise StratisCliNoChangeError("rename", namespace.new)

    @staticmethod
    def add_data_devices(namespace):
        """
        Add specified data devices to a pool.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        :raises StratisCliInUseOtherTierError:
        :raises StratisCliInUseSameTierError:
        :raises StratisCliPartialChangeError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager
        from ._data import Pool
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        blockdevs = frozenset(namespace.blockdevs)

        _check_opposite_tier(managed_objects, blockdevs, BlockDevTiers.Cache)

        _check_same_tier(
            namespace.pool_name, managed_objects, blockdevs, BlockDevTiers.Data
        )

        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        ((added, devs_added), rc, message) = Pool.Methods.AddDataDevs(
            get_object(pool_object_path), {"devices": list(blockdevs)}
        )
        if rc != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(rc, message)

        if not added or len(devs_added) < len(blockdevs):  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    "Expected to add the specified blockdevs to the data tier "
                    "in pool %s but stratisd reports that it did not actually "
                    "add some or all of the blockdevs requested"
                )
                % namespace.pool_name
            )

    @staticmethod
    def add_cache_devices(namespace):
        """
        Add specified cache devices to a pool.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        :raises StratisCliInUseOtherTierError:
        :raises StratisCliInUseSameTierError:
        :raises StratisCliPartialChangeError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager
        from ._data import Pool
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        blockdevs = frozenset(namespace.blockdevs)

        _check_opposite_tier(managed_objects, blockdevs, BlockDevTiers.Data)

        _check_same_tier(
            namespace.pool_name, managed_objects, blockdevs, BlockDevTiers.Cache
        )

        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        ((added, devs_added), rc, message) = Pool.Methods.AddCacheDevs(
            get_object(pool_object_path), {"devices": list(blockdevs)}
        )
        if rc != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(rc, message)

        if not added or len(devs_added) < len(blockdevs):  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    "Expected to add the specified blockdevs to the cache tier "
                    "in pool %s but stratisd reports that it did not actually "
                    "add some or all of the blockdevs requested"
                )
                % namespace.pool_name
            )
