# Copyright 2021 Red Hat, Inc.
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
Pool actions.
"""

# isort: STDLIB
import os
from collections import defaultdict
from itertools import tee
from uuid import UUID

# isort: THIRDPARTY
from justbytes import Range

from .._constants import YesOrNo
from .._error_codes import PoolAllocSpaceErrorCode, PoolErrorCode
from .._errors import (
    StratisCliEngineError,
    StratisCliIncoherenceError,
    StratisCliInUseOtherTierError,
    StratisCliInUseSameTierError,
    StratisCliNameConflictError,
    StratisCliNoChangeError,
    StratisCliPartialChangeError,
    StratisCliResourceNotFoundError,
)
from .._stratisd_constants import BlockDevTiers, PoolActionAvailability, StratisdErrors
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import (
    TABLE_FAILURE_STRING,
    TOTAL_USED_FREE,
    get_property,
    get_uuid_formatter,
    print_table,
    size_triple,
)
from ._utils import get_clevis_info


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
    # pylint: disable=import-outside-toplevel
    from ._data import MODev, MOPool, devs, pools

    pool_map = dict(
        (path, str(MOPool(info).Name()))
        for (path, info) in pools().search(managed_objects)
    )

    pools_to_blockdevs = defaultdict(list)
    for modev in (
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

    assert isinstance(pools_to_blockdevs, dict)
    if pools_to_blockdevs:
        raise StratisCliInUseOtherTierError(
            pools_to_blockdevs,
            BlockDevTiers.DATA
            if other_tier == BlockDevTiers.CACHE
            else BlockDevTiers.CACHE,
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
    if owned_by_current_pool != frozenset():
        raise StratisCliPartialChangeError(
            "add to cache" if this_tier == BlockDevTiers.CACHE else "add to data",
            to_be_added.difference(owned_by_current_pool),
            to_be_added.intersection(owned_by_current_pool),
        )

    owned_by_other_pools = dict(
        (pool, devnodes)
        for pool, devnodes in pools_to_blockdevs.items()
        if pool_name != pool
    )
    if owned_by_other_pools:
        raise StratisCliInUseSameTierError(owned_by_other_pools, this_tier)


def _fetch_stopped_pools_property(proxy):
    """
    Fetch the LockedPools property from stratisd.
    :param proxy: proxy to the top object in stratisd
    :return: a representation of unlocked devices
    :rtype: dict
    :raises StratisCliEngineError:
    """

    # pylint: disable=import-outside-toplevel
    from ._data import Manager

    return Manager.Properties.StoppedPools.Get(proxy)


class PoolActions:
    """
    Pool actions.
    """

    @staticmethod
    def create_pool(namespace):  # pylint: disable=too-many-locals
        """
        Create a stratis pool.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        :raises StratisCliNameConflictError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import Manager, ObjectManager, Pool, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        pool_name = namespace.pool_name
        blockdevs = frozenset([os.path.abspath(p) for p in namespace.blockdevs])

        names = pools(props={"Name": pool_name}).search(managed_objects)
        if next(names, None) is not None:
            raise StratisCliNameConflictError("pool", pool_name)

        _check_opposite_tier(managed_objects, blockdevs, BlockDevTiers.CACHE)

        _check_same_tier(pool_name, managed_objects, blockdevs, BlockDevTiers.DATA)

        clevis_info = get_clevis_info(namespace)

        (
            (changed, (pool_object_path, _)),
            return_code,
            message,
        ) = Manager.Methods.CreatePool(
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
                "clevis_info": (False, ("", ""))
                if clevis_info is None
                else (True, clevis_info),
            },
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if not changed:  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    f"Expected to create the specified pool {pool_name} but stratisd "
                    f"reports that it did not actually create the pool"
                )
            )

        if namespace.no_overprovision:
            Pool.Properties.Overprovisioning.Set(get_object(pool_object_path), False)

    @staticmethod
    def stop_pool(namespace):
        """
        Stop a pool.

        :raises StratisCliIncoherenceError:
        :raises StratisCliEngineError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import Manager, ObjectManager, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        pool_name = namespace.pool_name
        (pool_object_path, _) = next(
            pools(props={"Name": pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        ((stopped, _), return_code, message) = Manager.Methods.StopPool(
            proxy, {"pool": pool_object_path}
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if not stopped:  # pragma: no cover
            raise StratisCliIncoherenceError(
                f"Expected to stop pool with name {pool_name} but it was already stopped."
            )

    @staticmethod
    def start_pool(namespace):
        """
        Start a pool.

        :raises StratisCliIncoherenceError:
        :raises StratisCliEngineError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import Manager

        proxy = get_object(TOP_OBJECT)

        ((started, _), return_code, message) = Manager.Methods.StartPool(
            proxy,
            {
                "pool_uuid": str(namespace.pool_uuid),
                "unlock_method": (False, "")
                if namespace.unlock_method is None
                else (True, namespace.unlock_method),
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        if not started:
            raise StratisCliNoChangeError("start", namespace.pool_uuid)

    @staticmethod
    def init_cache(namespace):  # pylint: disable=too-many-locals
        """
        Initialize the cache of an existing stratis pool.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MODev, ObjectManager, Pool, devs, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        pool_name = namespace.pool_name
        (pool_object_path, _) = next(
            pools(props={"Name": pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )
        blockdevs = frozenset([os.path.abspath(p) for p in namespace.blockdevs])

        _check_opposite_tier(managed_objects, blockdevs, BlockDevTiers.DATA)

        _check_same_tier(pool_name, managed_objects, blockdevs, BlockDevTiers.CACHE)

        ((changed, devs_added), return_code, message) = Pool.Methods.InitCache(
            get_object(pool_object_path), {"devices": blockdevs}
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
                    f"Expected to add the specified blockdevs as cache to pool "
                    f"{namespace.pool_name} but stratisd reports that it did not "
                    f"actually add some or all of the blockdevs requested; "
                    f"devices added: ({', '.join(devnodes_added)}), "
                    f"devices requested: ({', '.join(blockdevs)})"
                )
            )

    @staticmethod
    def list_pools(namespace):
        """
        List Stratis pools.
        """
        # This method may be invoked as a result of the command line argument
        # "pool", without any options, in which case these attributes have not
        # been set.
        (stopped, pool_uuid) = (
            getattr(namespace, "stopped", False),
            getattr(namespace, "uuid", None),
        )

        uuid_formatter = get_uuid_formatter(namespace.unhyphenated_uuids)

        if stopped:
            return _List(uuid_formatter).list_stopped_pools(pool_uuid=pool_uuid)
        return _List(uuid_formatter).list_pools_default(pool_uuid=pool_uuid)

    @staticmethod
    def destroy_pool(namespace):
        """
        Destroy a stratis pool.

        If no pool exists, the method succeeds.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import Manager, ObjectManager, pools

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
                    f"Expected to destroy the specified pool {namespace.pool_name} but "
                    f"stratisd reports that it did not actually "
                    f"destroy the pool requested"
                )
            )

    @staticmethod
    def rename_pool(namespace):
        """
        Rename a pool.

        :raises StratisCliEngineError:
        :raises StratisCliNoChangeError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

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
        # pylint: disable=import-outside-toplevel
        from ._data import MODev, ObjectManager, Pool, devs, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        blockdevs = frozenset([os.path.abspath(p) for p in namespace.blockdevs])

        _check_opposite_tier(managed_objects, blockdevs, BlockDevTiers.CACHE)

        _check_same_tier(
            namespace.pool_name, managed_objects, blockdevs, BlockDevTiers.DATA
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
                    f"Expected to add the specified blockdevs to the data tier "
                    f"in pool {namespace.pool_name} but stratisd reports that it did not "
                    f"actually add some or all of the blockdevs requested; "
                    f"devices added: ({', '.join(devnodes_added)}), "
                    f"devices requested: ({', '.join(blockdevs)})"
                )
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
        # pylint: disable=import-outside-toplevel
        from ._data import MODev, ObjectManager, Pool, devs, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        blockdevs = frozenset([os.path.abspath(p) for p in namespace.blockdevs])

        _check_opposite_tier(managed_objects, blockdevs, BlockDevTiers.DATA)

        _check_same_tier(
            namespace.pool_name, managed_objects, blockdevs, BlockDevTiers.CACHE
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
                    f"Expected to add the specified blockdevs to the cache tier "
                    f"in pool {namespace.pool_name} but stratisd reports that it did not "
                    f"actually add some or all of the blockdevs requested; "
                    f"devices added: ({', '.join(devnodes_added)}), "
                    f"devices requested: ({', '.join(blockdevs)})"
                )
            )

    @staticmethod
    def extend_data(namespace):  # pylint: disable=too-many-locals
        """
        Extend the pool making use of the additional space offered by component
        devices. Exit immediately if something unexpected happens.

        :raises StratisCliPartialChangeError:
        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MODev, ObjectManager, Pool, devs, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        modevs = (
            MODev(info)
            for objpath, info in devs(props={"Pool": pool_object_path}).search(
                managed_objects
            )
        )

        def expandable(modev):
            """
            Return true if the new size is greater than total.

            :param MODev modev: blockdev representation
            :rtype: bool
            :returns: True if new physical size is greater than in-use size.
            """
            new_size = get_property(modev.NewPhysicalSize(), Range, None)
            return (
                False
                if new_size is None
                else new_size > Range(modev.TotalPhysicalSize())
            )

        if namespace.device_uuid == []:
            expand_modevs = (modev for modev in modevs if expandable(modev))

        else:
            device_uuids = frozenset(uuid.hex for uuid in namespace.device_uuid)
            expand_modevs = [modev for modev in modevs if modev.Uuid() in device_uuids]

            if len(expand_modevs) < len(device_uuids):
                missing_uuids = device_uuids.difference(
                    frozenset(UUID(modev.Uuid()) for modev in expand_modevs)
                )

                missing_uuids = ", ".join(str(UUID(uuid)) for uuid in missing_uuids)

                raise StratisCliResourceNotFoundError(
                    "extend-data", f"devices with UUIDs {missing_uuids}"
                )

            t_1, t_2 = tee(expand_modevs)
            expandable_modevs, unexpandable_modevs = (
                [modev for modev in t_1 if expandable(modev)],
                [modev for modev in t_2 if not expandable(modev)],
            )

            if unexpandable_modevs:
                raise StratisCliPartialChangeError(
                    "extend-data",
                    frozenset(str(UUID(modev.Uuid())) for modev in expandable_modevs),
                    frozenset(str(UUID(modev.Uuid())) for modev in unexpandable_modevs),
                )

            expand_modevs = expandable_modevs  # pragma: no cover

        for modev in expand_modevs:  # pragma: no cover
            (changed, return_code, message) = Pool.Methods.GrowPhysicalDevice(
                get_object(pool_object_path), {"dev": modev.Uuid()}
            )

            if return_code != StratisdErrors.OK:
                raise StratisCliEngineError(return_code, message)

            if not changed:
                raise StratisCliIncoherenceError(
                    (
                        f"Actual size of device with UUID {UUID(modev.Uuid())} "
                        "appeared to be different from in-use size but no "
                        "action was taken on the device."
                    )
                )

    @staticmethod
    def set_fs_limit(namespace):
        """
        Set the filesystem limit.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        Pool.Properties.FsLimit.Set(get_object(pool_object_path), namespace.amount)

    @staticmethod
    def set_overprovisioning_mode(namespace):
        """
        Set the overprovisioning mode.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

        decision = bool(YesOrNo.from_str(namespace.decision))

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        Pool.Properties.Overprovisioning.Set(get_object(pool_object_path), decision)

    @staticmethod
    def explain_code(namespace):
        """
        Print an explanation of pool error code.
        """
        print(PoolErrorCode.explain(namespace.code))


class _List:
    """
    Handle listing a pool.
    """

    def __init__(self, uuid_formatter):
        """
        Initialize a _List object.
        :param uuid_formatter: function to format a UUID str or UUID
        :param uuid_formatter: str or UUID -> str
        """
        self.uuid_formatter = uuid_formatter

    @staticmethod
    def _maybe_inconsistent(value, interp):
        """
        Take a value that represents possible inconsistency via result type.

        :param value: a tuple, second item is the value
        :param interp: a function to intepret the optional value
        :type value: bool * object
        :rtype: str
        """
        (real, value) = value
        return interp(value) if real else "inconsistent"

    @staticmethod
    def _interp_inconsistent_option(value):
        """
        Interpret a result that also may not exist.
        """

        def my_func(value):
            (exists, value) = value
            return str(value) if exists else "N/A"

        return _List._maybe_inconsistent(value, my_func)

    def _print_detail_view(self, pool_uuid, mopool):
        """
        Print the detailed view for a single pool.

        :param UUID uuid: the pool uuid
        :param MOPool mopool: properties of the pool
        """
        encrypted = mopool.Encrypted()

        print(f"UUID: {self.uuid_formatter(pool_uuid)}")
        print(f"Name: {mopool.Name()}")
        print(
            f"Actions Allowed: "
            f"{PoolActionAvailability.from_str(mopool.AvailableActions())}"
        )
        print(f"Cache: {'Yes' if mopool.HasCache() else 'No'}")
        print(f"Filesystem Limit: {mopool.FsLimit()}")
        print(
            f"Allows Overprovisioning: "
            f"{'Yes' if mopool.Overprovisioning() else 'No'}"
        )

        key_description_str = (
            _List._interp_inconsistent_option(mopool.KeyDescription())
            if encrypted
            else "unencrypted"
        )
        print(f"Key Description: {key_description_str}")

        clevis_info_str = (
            _List._interp_inconsistent_option(mopool.ClevisInfo())
            if encrypted
            else "unencrypted"
        )
        print(f"Clevis Configuration: {clevis_info_str}")

        total_physical_used = get_property(mopool.TotalPhysicalUsed(), Range, None)

        print("Space Usage:")
        print(f"Fully Allocated: {'Yes' if mopool.NoAllocSpace() else 'No'}")
        print(f"    Size: {Range(mopool.TotalPhysicalSize())}")
        print(f"    Allocated: {Range(mopool.AllocatedSize())}")

        total_physical_used = get_property(mopool.TotalPhysicalUsed(), Range, None)
        total_physical_used_str = (
            TABLE_FAILURE_STRING if total_physical_used is None else total_physical_used
        )

        print(f"    Used: {total_physical_used_str}")

    def list_pools_default(self, *, pool_uuid=None):
        """
        List all pools that are listed by default. These are all started pools.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MOPool, ObjectManager, pools

        proxy = get_object(TOP_OBJECT)

        def physical_size_triple(mopool):
            """
            Calculate the triple to display for total physical size.

            The format is total/used/free where the display value for each
            member of the tuple are chosen automatically according to justbytes'
            configuration.

            :param mopool: an object representing all the properties of the pool
            :type mopool: MOPool
            :returns: a string to display in the resulting list output
            :rtype: str
            """
            total_physical_size = Range(mopool.TotalPhysicalSize())
            total_physical_used = get_property(mopool.TotalPhysicalUsed(), Range, None)
            return size_triple(total_physical_size, total_physical_used)

        def properties_string(mopool):
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

                :param has_property: whether the property is true or false
                :type has_property: bool or NoneType
                :param str code: the code to generate the string for
                :returns: the generated string
                :rtype: str
                """
                if has_property == True:  # pylint: disable=singleton-comparison
                    prefix = " "
                elif has_property == False:  # pylint: disable=singleton-comparison
                    prefix = "~"
                # This is only going to occur if the engine experiences an
                # error while calculating a property or if our code has a bug.
                else:  # pragma: no cover
                    prefix = "?"
                return prefix + code

            props_list = [
                (mopool.HasCache(), "Ca"),
                (mopool.Encrypted(), "Cr"),
                (mopool.Overprovisioning(), "Op"),
            ]
            return ",".join(gen_string(x, y) for x, y in props_list)

        def alert_string(mopool):
            """
            Alert information to display, if any

            :param mopool: object to access pool properties

            :returns: string w/ alert information, "" if no alert
            :rtype: str
            """
            action_availability = PoolActionAvailability.from_str(
                mopool.AvailableActions()
            )
            availability_error_codes = (
                action_availability.pool_maintenance_error_codes()
            )

            no_alloc_space_error_codes = (
                [PoolAllocSpaceErrorCode.NO_ALLOC_SPACE]
                if mopool.NoAllocSpace()
                else []
            )

            error_codes = availability_error_codes + no_alloc_space_error_codes

            return ", ".join(sorted(str(code) for code in error_codes))

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        if pool_uuid is None:
            pools_with_props = [
                MOPool(info) for objpath, info in pools().search(managed_objects)
            ]

            tables = [
                (
                    mopool.Name(),
                    physical_size_triple(mopool),
                    properties_string(mopool),
                    self.uuid_formatter(mopool.Uuid()),
                    alert_string(mopool),
                )
                for mopool in pools_with_props
            ]

            print_table(
                [
                    "Name",
                    TOTAL_USED_FREE,
                    "Properties",
                    "UUID",
                    "Alerts",
                ],
                sorted(tables, key=lambda entry: entry[0]),
                ["<", ">", ">", ">", "<"],
            )

        else:
            this_uuid = pool_uuid.hex
            mopool = MOPool(
                next(
                    pools(props={"Uuid": this_uuid})
                    .require_unique_match(True)
                    .search(managed_objects)
                )[1]
            )

            self._print_detail_view(pool_uuid, mopool)

    def list_stopped_pools(self, *, pool_uuid=None):
        """
        List stopped pools.
        """

        proxy = get_object(TOP_OBJECT)

        stopped_pools = _fetch_stopped_pools_property(proxy)

        def interp_clevis(value):
            """
            Intepret Clevis info for table display.
            """

            def my_func(value):
                (exists, value) = value
                return "present" if exists else "N/A"

            return _List._maybe_inconsistent(value, my_func)

        def unencrypted_string(value, interp):
            """
            Get a cell value or "unencrypted" if None. Apply interp
            function to the value.

            :param value: some value
            :type value: str or NoneType
            :param interp_option: function to interpret optional value
            :type interp_option: object -> str
            :rtype: str
            """
            return "unencrypted" if value is None else interp(value)

        if pool_uuid is None:
            tables = [
                (
                    self.uuid_formatter(pool_uuid),
                    str(len(info["devs"])),
                    unencrypted_string(
                        info.get("key_description"), _List._interp_inconsistent_option
                    ),
                    unencrypted_string(info.get("clevis_info"), interp_clevis),
                )
                for (pool_uuid, info) in stopped_pools.items()
            ]

            print_table(
                ["UUID", "# Devices", "Key Description", "Clevis"],
                sorted(tables, key=lambda entry: entry[0]),
                ["<", ">", "<", "<"],
            )

        else:
            this_uuid = pool_uuid.hex
            stopped_pool = next(
                (info for (uuid, info) in stopped_pools.items() if uuid == this_uuid),
                None,
            )

            if stopped_pool is None:
                raise StratisCliResourceNotFoundError("list", this_uuid)

            print(f"UUID: {self.uuid_formatter(this_uuid)}")

            key_description_str = unencrypted_string(
                stopped_pool.get("key_description"), _List._interp_inconsistent_option
            )
            print(f"Key Description: {key_description_str}")

            clevis_info_str = unencrypted_string(
                stopped_pool.get("clevis_info"), _List._interp_inconsistent_option
            )
            print(f"Clevis Configuration: {clevis_info_str}")

            print("Devices:")
            for dev in stopped_pool["devs"]:
                print(f"{self.uuid_formatter(dev['uuid'])}  {dev['devnode']}")
