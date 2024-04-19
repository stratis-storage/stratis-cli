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
import json
import os
from collections import defaultdict
from itertools import tee
from uuid import UUID

# isort: THIRDPARTY
from justbytes import Range

from .._constants import PoolIdType
from .._error_codes import PoolErrorCode
from .._errors import (
    StratisCliEngineError,
    StratisCliFsLimitChangeError,
    StratisCliHasCacheChangeError,
    StratisCliIncoherenceError,
    StratisCliInUseOtherTierError,
    StratisCliInUseSameTierError,
    StratisCliNameConflictError,
    StratisCliNoChangeError,
    StratisCliNoDeviceSizeChangeError,
    StratisCliOverprovisionChangeError,
    StratisCliPartialChangeError,
    StratisCliResourceNotFoundError,
)
from .._stratisd_constants import BlockDevTiers, StratisdErrors
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import get_property, get_uuid_formatter
from ._list_pool import list_pools
from ._utils import ClevisInfo, PoolSelector


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
            (
                BlockDevTiers.DATA
                if other_tier == BlockDevTiers.CACHE
                else BlockDevTiers.CACHE
            ),
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

        clevis_info = ClevisInfo.get_info_from_namespace(namespace)

        (
            (changed, (pool_object_path, _)),
            return_code,
            message,
        ) = Manager.Methods.CreatePool(
            proxy,
            {
                "name": pool_name,
                "devices": blockdevs,
                "key_desc": (
                    (True, namespace.key_desc)
                    if namespace.key_desc is not None
                    else (False, "")
                ),
                "clevis_info": (
                    (False, ("", ""))
                    if clevis_info is None
                    else (True, (clevis_info.pin, json.dumps(clevis_info.config)))
                ),
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
        from ._data import Manager

        proxy = get_object(TOP_OBJECT)

        (pool_id, id_type) = (
            (namespace.uuid.hex, "uuid")
            if getattr(namespace, "name") is None
            else (namespace.name, "name")
        )

        ((stopped, _), return_code, message) = Manager.Methods.StopPool(
            proxy,
            {
                "id": pool_id,
                "id_type": id_type,
            },
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if not stopped:
            raise StratisCliNoChangeError("stop", pool_id)

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

        (pool_id, id_type) = (
            (namespace.uuid.hex, "uuid")
            if getattr(namespace, "name") is None
            else (namespace.name, "name")
        )

        ((started, _), return_code, message) = Manager.Methods.StartPool(
            proxy,
            {
                "id": pool_id,
                "id_type": id_type,
                "unlock_method": (
                    (False, "")
                    if namespace.unlock_method is None
                    else (True, str(namespace.unlock_method))
                ),
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        if not started:
            raise StratisCliNoChangeError("start", pool_id)

    @staticmethod
    def init_cache(namespace):  # pylint: disable=too-many-locals
        """
        Initialize the cache of an existing stratis pool.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MODev, MOPool, ObjectManager, Pool, devs, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        pool_name = namespace.pool_name
        (pool_object_path, pool_info) = next(
            pools(props={"Name": pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        if MOPool(pool_info).HasCache():
            raise StratisCliHasCacheChangeError()

        blockdevs = frozenset([os.path.abspath(p) for p in namespace.blockdevs])

        _check_opposite_tier(managed_objects, blockdevs, BlockDevTiers.DATA)

        _check_same_tier(pool_name, managed_objects, blockdevs, BlockDevTiers.CACHE)

        ((changed, devs_added), return_code, message) = Pool.Methods.InitCache(
            get_object(pool_object_path), {"devices": blockdevs}
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
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
        (stopped, pool_uuid, pool_name) = (
            getattr(namespace, "stopped", False),
            getattr(namespace, "uuid", None),
            getattr(namespace, "name", None),
        )

        uuid_formatter = get_uuid_formatter(namespace.unhyphenated_uuids)

        selection = (
            (None if pool_name is None else PoolSelector(PoolIdType.NAME, pool_name))
            if pool_uuid is None
            else PoolSelector(PoolIdType.UUID, pool_uuid)
        )

        return list_pools(uuid_formatter, stopped=stopped, selection=selection)

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

        def expand(pool_proxy, modev):  # pragma: no cover
            """
            Expand a pool by extending exactly one expandable device in the
            pool.

            :param pool_proxy: dbus proxy object for the pool
            :param MoDev modev: represents D-Bus information on a single device
            """
            (changed, return_code, message) = Pool.Methods.GrowPhysicalDevice(
                pool_proxy, {"dev": modev.Uuid()}
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

        def get_devices_to_expand(device_uuids, modevs):
            """
            Calculate devices to expand
            :param device_uuids: a list of device uuids, if empty expand all
            :type device_uuids: list of UUID
            :param modevs: MODev objects representing all devices in the pool
            :type modevs: list of MODev
            :return: list of MODev objects representing devices to expand
            """
            if device_uuids == []:
                expand_modevs = [modev for modev in modevs if expandable(modev)]
            else:
                device_uuids = frozenset(uuid.hex for uuid in device_uuids)
                expand_modevs = [
                    modev for modev in modevs if modev.Uuid() in device_uuids
                ]
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

                if unexpandable_modevs != []:  # pragma: no cover
                    raise StratisCliPartialChangeError(
                        "extend-data",
                        frozenset(
                            str(UUID(modev.Uuid())) for modev in expandable_modevs
                        ),
                        frozenset(
                            str(UUID(modev.Uuid())) for modev in unexpandable_modevs
                        ),
                    )

            return expand_modevs

        expand_modevs = get_devices_to_expand(namespace.device_uuid, modevs)

        assert isinstance(expand_modevs, list)
        if expand_modevs == []:
            raise StratisCliNoDeviceSizeChangeError()

        pool_proxy = get_object(pool_object_path)  # pragma: no cover
        for modev in expand_modevs:  # pragma: no cover
            expand(pool_proxy, modev)

    @staticmethod
    def set_fs_limit(namespace):
        """
        Set the filesystem limit.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MOPool, ObjectManager, Pool, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, pool_info) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        if namespace.amount == MOPool(pool_info).FsLimit():
            raise StratisCliFsLimitChangeError(namespace.amount)

        Pool.Properties.FsLimit.Set(get_object(pool_object_path), namespace.amount)

    @staticmethod
    def set_overprovisioning_mode(namespace):
        """
        Set the overprovisioning mode.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MOPool, ObjectManager, Pool, pools

        decision = bool(namespace.decision)

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, pool_info) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        if decision == MOPool(pool_info).Overprovisioning():
            raise StratisCliOverprovisionChangeError(decision)

        Pool.Properties.Overprovisioning.Set(get_object(pool_object_path), decision)

    @staticmethod
    def explain_code(namespace):
        """
        Print an explanation of pool error code.
        """
        print(PoolErrorCode.explain(namespace.code))
