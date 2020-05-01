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

# isort: STDLIB
from collections import defaultdict

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
    :param to_be_added: the blockdevs to be added
    :type to_be_added: frozenset of str
    :param tier: tier to search for blockdevs to be added
    :type tier: _stratisd_constants.BlockDevTiers
    :returns: a map of pool names to sets of strings containing blockdevs they own
    :rtype: dict of str * frozenset of str
    """
    from ._data import MODev
    from ._data import MOPool
    from ._data import devs
    from ._data import pools

    pool_map = dict(
        (path, str(MOPool(info).Name()))
        for (path, info) in pools().search(managed_objects)
    )

    pools_to_blockdevs = defaultdict(list)
    for modev in (
        # pylint: disable=bad-continuation
        modev
        for modev in (
            MODev(info)
            for (_, info) in devs(props={"Tier": tier}).search(managed_objects)
        )
        if str(modev.Devnode()) in to_be_added
    ):
        pools_to_blockdevs[pool_map[modev.Pool()]].append(str(modev.Devnode()))

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
    :param this_tier: the tier requested
    :type this_tier: _stratisd_constants.BlockDevTiers
    :raises StratisCliPartialChangeError: if blockdevs are used by this tier
    :raises StratisCliInUseSameTierError: if blockdevs are used by this tier in another pool
    """
    pools_to_blockdevs = _generate_pools_to_blockdevs(
        managed_objects, to_be_added, this_tier
    )

    owned_by_current_pool = frozenset(pools_to_blockdevs.get(pool_name, []))
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
        from ._data import Manager
        from ._data import ObjectManager
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        pool_name = namespace.pool_name
        names = pools(props={"Name": pool_name}).search(managed_objects)
        blockdevs = frozenset(namespace.blockdevs)
        if list(names) != []:
            raise StratisCliNameConflictError("pool", pool_name)

        _check_opposite_tier(managed_objects, blockdevs, BlockDevTiers.Cache)

        _check_same_tier(pool_name, managed_objects, blockdevs, BlockDevTiers.Data)

        ((changed, (_, _)), return_code, message) = Manager.Methods.CreatePool(
            proxy,
            {
                "name": pool_name,
                "redundancy": (True, 0),
                "devices": blockdevs,
                "key_desc": (
                    (True, namespace.key_desc)
                    if namespace.key_desc is not None
                    else (False, "")
                ),
            },
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if not changed:  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    "Expected to create the specified pool %s but stratisd "
                    "reports that it did not actually create the pool"
                )
                % pool_name
            )

    @staticmethod
    def init_cache(namespace):  # pylint: disable=too-many-locals
        """
        Initialize the cache of an existing stratis pool.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        """
        from ._data import MODev
        from ._data import ObjectManager
        from ._data import Pool
        from ._data import devs
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        pool_name = namespace.pool_name
        (pool_object_path, _) = next(
            pools(props={"Name": pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )
        blockdevs = frozenset(namespace.blockdevs)

        _check_opposite_tier(managed_objects, blockdevs, BlockDevTiers.Data)

        _check_same_tier(pool_name, managed_objects, blockdevs, BlockDevTiers.Cache)

        ((changed, devs_added), return_code, message) = Pool.Methods.InitCache(
            get_object(pool_object_path), {"devices": namespace.blockdevs}
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        if not changed or len(devs_added) < len(blockdevs):  # pragma: no cover
            devnodes_added = [
                MODev(info).Devnode()
                for (object_path, info) in devs(
                    props={"Pool": pool_object_path}
                ).search(ObjectManager.Methods.GetManagedObjects(proxy, {}))
                if object_path in devs_added
            ]
            raise StratisCliIncoherenceError(
                (
                    "Expected to add the specified blockdevs as cache "
                    "to pool %s but stratisd reports that it did not actually "
                    "add some or all of the blockdevs requested; devices "
                    "added: (%s), devices requested: (%s)"
                )
                % (namespace.pool_name, ", ".join(devnodes_added), ", ".join(blockdevs))
            )

    @staticmethod
    def list_pools(_):
        """
        List all stratis pools.

        :raises StratisCliEngineError:
        """
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

        def properties_string(mopool, props_map):
            """
            Make a string encoding some important properties of the pool

            :param mopool: an object representing all the properties of the pool
            :type mopool: MOPool
            :param props_map: a map of properties returned by GetAllProperties
            :type props_map: dict of str * any
            """

            def gen_string(has_property, code):
                """
                Generate the display string for a boolean property

                :param bool has_property: whether the property is true or false
                :param str code: the code to generate the string for
                :returns: the generated string
                :rtype: str
                """
                return " " + code if has_property else "~" + code

            prop_list = []
            prop_list.append(
                gen_string(
                    fetch_property(POOL_INTERFACE, props_map, "HasCache", lambda x: x),
                    "Ca",
                )
            )
            prop_list.append(gen_string(mopool.Encrypted(), "Cr"))
            return ",".join(prop_list)

        tables = [
            (
                mopool.Name(),
                physical_size_triple(props),
                properties_string(mopool, props),
            )
            for props, mopool in pools_with_props
        ]

        print_table(
            ["Name", "Total Physical", "Properties"],
            sorted(tables, key=lambda entry: entry[0]),
            ["<", ">", ">"],
        )

    @staticmethod
    def destroy_pool(namespace):
        """
        Destroy a stratis pool.

        If no pool exists, the method succeeds.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
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

        ((changed, _), return_code, message) = Manager.Methods.DestroyPool(
            proxy, {"pool": pool_object_path}
        )

        # This branch can be covered, since the engine will return an error
        # if the pool can not be destroyed because it has filesystems.
        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

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

        ((changed, _), return_code, message) = Pool.Methods.SetName(
            get_object(pool_object_path), {"name": namespace.new}
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if not changed:
            raise StratisCliNoChangeError("rename", namespace.new)

    @staticmethod
    def add_data_devices(namespace):  # pylint: disable=too-many-locals
        """
        Add specified data devices to a pool.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        :raises StratisCliInUseOtherTierError:
        :raises StratisCliInUseSameTierError:
        :raises StratisCliPartialChangeError:
        """
        from ._data import MODev
        from ._data import ObjectManager
        from ._data import Pool
        from ._data import devs
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

        ((added, devs_added), return_code, message) = Pool.Methods.AddDataDevs(
            get_object(pool_object_path), {"devices": list(blockdevs)}
        )
        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if not added or len(devs_added) < len(blockdevs):  # pragma: no cover
            devnodes_added = [
                MODev(info).Devnode()
                for (object_path, info) in devs(
                    props={"Pool": pool_object_path}
                ).search(ObjectManager.Methods.GetManagedObjects(proxy, {}))
                if object_path in devs_added
            ]
            raise StratisCliIncoherenceError(
                (
                    "Expected to add the specified blockdevs to the data tier "
                    "in pool %s but stratisd reports that it did not actually "
                    "add some or all of the blockdevs requested; devices "
                    "added: (%s), devices requested: (%s)"
                )
                % (namespace.pool_name, ", ".join(devnodes_added), ", ".join(blockdevs))
            )

    @staticmethod
    def add_cache_devices(namespace):  # pylint: disable=too-many-locals
        """
        Add specified cache devices to a pool.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        :raises StratisCliInUseOtherTierError:
        :raises StratisCliInUseSameTierError:
        :raises StratisCliPartialChangeError:
        """
        from ._data import MODev
        from ._data import ObjectManager
        from ._data import Pool
        from ._data import devs
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

        ((added, devs_added), return_code, message) = Pool.Methods.AddCacheDevs(
            get_object(pool_object_path), {"devices": list(blockdevs)}
        )
        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        if not added or len(devs_added) < len(blockdevs):  # pragma: no cover
            devnodes_added = [
                MODev(info).Devnode()
                for (object_path, info) in devs(
                    props={"Pool": pool_object_path}
                ).search(ObjectManager.Methods.GetManagedObjects(proxy, {}))
                if object_path in devs_added
            ]
            raise StratisCliIncoherenceError(
                (
                    "Expected to add the specified blockdevs to the cache tier "
                    "in pool %s but stratisd reports that it did not actually "
                    "add some or all of the blockdevs requested; devices "
                    "added: (%s), devices requested: (%s)"
                )
                % (namespace.pool_name, ", ".join(devnodes_added), ", ".join(blockdevs))
            )
