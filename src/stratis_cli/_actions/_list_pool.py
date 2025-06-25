# Copyright 2022 Red Hat, Inc.
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
from abc import ABC, abstractmethod
from typing import List, Optional, Union

# isort: THIRDPARTY
from justbytes import Range

from .._error_codes import (
    PoolAllocSpaceErrorCode,
    PoolDeviceSizeChangeCode,
    PoolEncryptionErrorCode,
    PoolErrorCodeType,
)
from .._errors import StratisCliResourceNotFoundError
from .._stratisd_constants import MetadataVersion, PoolActionAvailability
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import (
    TABLE_FAILURE_STRING,
    TOTAL_USED_FREE,
    get_property,
    print_table,
    size_triple,
)
from ._utils import (
    EncryptionInfoClevis,
    EncryptionInfoKeyDescription,
    PoolFeature,
    StoppedPool,
    fetch_stopped_pools_property,
)


def _metadata_version(mopool) -> Optional[MetadataVersion]:
    try:
        return MetadataVersion(int(mopool.MetadataVersion()))
    except ValueError:  # pragma: no cover
        return None


def _volume_key_loaded(mopool) -> Union[tuple[bool, bool], tuple[bool, str]]:
    """
    The string result is an error message indicating that the volume key
    state is unknown.
    """
    result = mopool.VolumeKeyLoaded()
    if isinstance(result, int):
        return (True, bool(result))
    return (False, str(result))  # pragma: no cover


# This method is only used with legacy pools
def _non_existent_or_inconsistent_to_str(
    value,
    *,
    inconsistent_str="inconsistent",
    non_existent_str="N/A",
    interp=lambda x: str(x),  # pylint: disable=unnecessary-lambda
):  # pragma: no cover
    """
    Process dbus result that encodes both inconsistency and existence of the
    value.

    :param EncryptionInfo value: a dbus result
    :param str inconsistent_str: value to return if inconsistent
    :param str non_existent_str: value to return if non-existent
    :param interp: how to interpret the value if it exists and is consistent
    :returns: a string to print
    :rtype: str
    """
    if not value.consistent():
        return inconsistent_str

    value = value.value

    if value is None:
        return non_existent_str

    return interp(value)


class TokenSlotInfo:  # pylint: disable=too-few-public-methods
    """
    Just a class to merge info about two different ways of occupying LUKS
    token slots into one, so that the two different ways can be sorted by
    token and then printed.
    """

    def __init__(self, token_slot, *, key=None, clevis=None):
        """
        Initialize either information about a key or about a Clevis
        configuration for purposes of printing later.

        :param int token_slot: token slot
        :param str key: key
        :param clevis: clevis configuration
        :type clevis: pair of pin and configuration, str * json
        """
        assert (key is None) ^ (clevis is None)

        self.token_slot = token_slot
        self.key = key
        self.clevis = clevis

    def __str__(self):
        return f"Token Slot: {self.token_slot}{os.linesep}" + (
            f"    Key Description: {self.key}"
            if self.clevis is None
            else (
                f"    Clevis Pin: {self.clevis[0]}{os.linesep}"
                f"    Clevis Configuration: {self.clevis[1]}"
            )
        )


class DefaultAlerts:  # pylint: disable=too-few-public-methods
    """
    Alerts to display for a started pool.
    """

    def __init__(self, devs):
        """
        The initializer.

        :param devs: result of GetManagedObjects
        """
        (self.increased, self.decreased) = DefaultAlerts._pools_with_changed_devs(devs)

    def alert_codes(self, pool_object_path, mopool) -> List[PoolErrorCodeType]:
        """
        Return error code objects for a pool.

        :param mopool: object to access pool properties

        :returns: list of PoolErrorCode
        """
        action_availability = PoolActionAvailability[str(mopool.AvailableActions())]
        availability_error_codes = action_availability.pool_maintenance_error_codes()

        no_alloc_space_error_codes = (
            [PoolAllocSpaceErrorCode.NO_ALLOC_SPACE] if mopool.NoAllocSpace() else []
        )

        device_size_changed_codes = DefaultAlerts._from_sets(
            pool_object_path, self.increased, self.decreased
        )

        metadata_version = _metadata_version(mopool)

        (vkl_is_bool, volume_key_loaded) = _volume_key_loaded(mopool)

        pool_encryption_error_codes = (
            [PoolEncryptionErrorCode.VOLUME_KEY_NOT_LOADED]
            if metadata_version is MetadataVersion.V2
            and mopool.Encrypted()
            and vkl_is_bool
            and not volume_key_loaded
            else []
        ) + (
            [PoolEncryptionErrorCode.VOLUME_KEY_STATUS_UNKNOWN]
            if metadata_version is MetadataVersion.V2
            and mopool.Encrypted()
            and not vkl_is_bool
            else []
        )

        return (
            availability_error_codes
            + no_alloc_space_error_codes
            + device_size_changed_codes
            + pool_encryption_error_codes
        )

    @staticmethod
    def _pools_with_changed_devs(devs_to_search):
        """
        Returns a tuple of sets containing (1) pools that have a device that
        has increased in size and (2) pools that have a device that has
        decreased in size.

        A pool may occupy both sets if one device has increased and one has
        decreased.

        :param devs_to_search: an iterable of device objects
        :returns: a pair of sets
        :rtype: tuple of (set of ObjectPath)
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MODev

        (increased, decreased) = (set(), set())
        for _, info in devs_to_search:
            modev = MODev(info)
            size = Range(modev.TotalPhysicalSize())
            observed_size = get_property(modev.NewPhysicalSize(), Range, size)
            if observed_size > size:  # pragma: no cover
                increased.add(modev.Pool())
            if observed_size < size:  # pragma: no cover
                decreased.add(modev.Pool())

        return (increased, decreased)

    @staticmethod
    def _from_sets(
        pool_object_path, increased, decreased
    ) -> List[PoolDeviceSizeChangeCode]:
        """
        Get the code from sets and one pool object path.

        :param pool_object_path: the pool object path
        :param increased: pools that have devices that have increased in size
        :type increased: set of object path
        :param decreased: pools that have devices that have decrease in size
        :type increased: set of object path

        :returns: the codes
        """
        if (
            pool_object_path in increased and pool_object_path in decreased
        ):  # pragma: no cover
            return [
                PoolDeviceSizeChangeCode.DEVICE_SIZE_INCREASED,
                PoolDeviceSizeChangeCode.DEVICE_SIZE_DECREASED,
            ]
        if pool_object_path in increased:  # pragma: no cover
            return [PoolDeviceSizeChangeCode.DEVICE_SIZE_INCREASED]
        if pool_object_path in decreased:  # pragma: no cover
            return [PoolDeviceSizeChangeCode.DEVICE_SIZE_DECREASED]
        return []


def list_pools(uuid_formatter, *, stopped=False, selection=None):
    """
    List the specified information about pools.
    :param uuid_formatter: how to format UUIDs
    :type uuid_formatter: (str or UUID) -> str
    :param bool stopped: True if stopped pools should be listed, else False
    :param PoolId selection: how to select pools to list
    """
    if stopped:
        if selection is None:
            klass = StoppedTable(uuid_formatter)
        else:
            klass = StoppedDetail(uuid_formatter, selection)
    else:
        if selection is None:
            klass = DefaultTable(uuid_formatter)
        else:
            klass = DefaultDetail(uuid_formatter, selection)

    klass.display()


def _clevis_to_str(clevis_info):  # pragma: no cover
    """
    :param ClevisInfo clevis_info: the Clevis info to stringify
    :return: a string that represents the clevis info
    :rtype: str
    """

    config_string = " ".join(
        f"{key}: {value}" for key, value in clevis_info.config.items()
    )
    return f"{clevis_info.pin}   {config_string}"


class ListPool(ABC):  # pylint:disable=too-few-public-methods
    """
    Handle listing a pool or pools.
    """

    @abstractmethod
    def display(self):
        """
        List the pools.
        """


class Default(ListPool):  # pylint: disable=too-few-public-methods
    """
    Handle listing the pools that are listed by default.
    """


class DefaultDetail(Default):  # pylint: disable=too-few-public-methods
    """
    List one pool with a detail view.
    """

    def __init__(self, uuid_formatter, selection):
        """
        Initializer.
        :param uuid_formatter: function to format a UUID str or UUID
        :param uuid_formatter: str or UUID -> str
        :param PoolId selection: how to select pools to list
        """
        self.uuid_formatter = uuid_formatter
        self.selection = selection

    def _print_detail_view(
        self, pool_object_path, mopool, alerts: DefaultAlerts
    ):  # pylint: disable=too-many-locals
        """
        Print the detailed view for a single pool.

        :param UUID uuid: the pool uuid
        :param pool_object_path: object path of the pool
        :param MOPool mopool: properties of the pool
        :param DefaultAlerts alerts: pool alerts
        """
        encrypted = mopool.Encrypted()

        print(f"UUID: {self.uuid_formatter(mopool.Uuid())}")
        print(f"Name: {mopool.Name()}")

        alert_summary = [
            f"{code}: {code.summarize()}"
            for code in alerts.alert_codes(pool_object_path, mopool)
        ]
        print(f"Alerts: {len(alert_summary)}")
        for line in alert_summary:  # pragma: no cover
            print(f"     {line}")

        metadata_version = _metadata_version(mopool)

        print(
            f'Metadata Version: {"none" if metadata_version is None else metadata_version}'
        )

        print(
            f"Actions Allowed: "
            f"{PoolActionAvailability[str(mopool.AvailableActions())].name}"
        )
        print(f"Cache: {'Yes' if mopool.HasCache() else 'No'}")
        print(f"Filesystem Limit: {mopool.FsLimit()}")
        print(
            f"Allows Overprovisioning: "
            f"{'Yes' if mopool.Overprovisioning() else 'No'}"
        )

        if encrypted:
            print("Encryption Enabled: Yes")

            if metadata_version is MetadataVersion.V1:  # pragma: no cover
                key_description_str = _non_existent_or_inconsistent_to_str(
                    EncryptionInfoKeyDescription(mopool.KeyDescriptions())
                )
                print(f"    Key Description: {key_description_str}")

                clevis_info_str = _non_existent_or_inconsistent_to_str(
                    EncryptionInfoClevis(mopool.ClevisInfos()),
                    interp=_clevis_to_str,
                )
                print(f"    Clevis Configuration: {clevis_info_str}")
            elif metadata_version is MetadataVersion.V2:
                encryption_infos = sorted(
                    [
                        TokenSlotInfo(token_slot, key=str(description))
                        for token_slot, description in mopool.KeyDescriptions()
                    ]
                    + [
                        TokenSlotInfo(
                            token_slot, clevis=(str(pin), json.loads(str(config)))
                        )
                        for token_slot, (pin, config) in mopool.ClevisInfos()
                    ],
                    key=lambda x: x.token_slot,
                )

                free_valid, free = mopool.FreeTokenSlots()
                print(
                    f'    Free Token Slots Remaining: {int(free) if free_valid else "<UNKNOWN>"}'
                )

                for info in encryption_infos:
                    for line in str(info).split(os.linesep):
                        print(f"    {line}")
            else:  # pragma: no cover
                pass
        else:
            print("Encryption Enabled: No")

        total_physical_used = get_property(mopool.TotalPhysicalUsed(), Range, None)

        print(f"Fully Allocated: {'Yes' if mopool.NoAllocSpace() else 'No'}")
        print(f"    Size: {Range(mopool.TotalPhysicalSize())}")
        print(f"    Allocated: {Range(mopool.AllocatedSize())}")

        total_physical_used = get_property(mopool.TotalPhysicalUsed(), Range, None)
        total_physical_used_str = (
            TABLE_FAILURE_STRING if total_physical_used is None else total_physical_used
        )

        print(f"    Used: {total_physical_used_str}")

    def display(self):
        """
        List a single pool in detail.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MOPool, ObjectManager, devs, pools

        proxy = get_object(TOP_OBJECT)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, mopool) = next(
            pools(props=self.selection.managed_objects_key())
            .require_unique_match(True)
            .search(managed_objects)
        )

        alerts = DefaultAlerts(
            devs(props={"Pool": pool_object_path}).search(managed_objects)
        )

        self._print_detail_view(pool_object_path, MOPool(mopool), alerts)


class DefaultTable(Default):  # pylint: disable=too-few-public-methods
    """
    List several pools with a table view.
    """

    def __init__(self, uuid_formatter):
        """
        Initializer.
        :param uuid_formatter: function to format a UUID str or UUID
        :param uuid_formatter: str or UUID -> str
        """
        self.uuid_formatter = uuid_formatter

    def display(self):
        """
        List pools in table view.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MOPool, ObjectManager, devs, pools

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

                :param bool has_property: whether the property is true or false
                :param str code: the code to generate the string for
                :returns: the generated string
                :rtype: str
                """
                return (" " if has_property else "~") + code

            metadata_version = _metadata_version(mopool)

            props_list = [
                (metadata_version in (MetadataVersion.V1, None), "Le"),
                (bool(mopool.HasCache()), "Ca"),
                (bool(mopool.Encrypted()), "Cr"),
                (bool(mopool.Overprovisioning()), "Op"),
            ]
            return ",".join(gen_string(x, y) for x, y in props_list)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        alerts = DefaultAlerts(devs().search(managed_objects))

        pools_with_props = [
            (objpath, MOPool(info)) for objpath, info in pools().search(managed_objects)
        ]

        tables = [
            (
                mopool.Name(),
                physical_size_triple(mopool),
                properties_string(mopool),
                self.uuid_formatter(mopool.Uuid()),
                ", ".join(
                    sorted(
                        str(code)
                        for code in alerts.alert_codes(pool_object_path, mopool)
                    )
                ),
            )
            for (pool_object_path, mopool) in pools_with_props
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


class Stopped(ListPool):  # pylint: disable=too-few-public-methods
    """
    Support for listing stopped pools.
    """

    @staticmethod
    def _pool_name(maybe_value):
        """
        Return formatted string for pool name.

        :param maybe_value: the pool name
        :type maybe_value: str or NoneType
        """
        return "<UNAVAILABLE>" if maybe_value is None else maybe_value

    @staticmethod
    def _metadata_version_str(maybe_value):
        """
        Return formatted string for metadata version.

        :param maybe_value: the metadata version
        :type maybe_value: int or NoneType
        """
        return "<MIXED>" if maybe_value is None else str(maybe_value)


class StoppedDetail(Stopped):  # pylint: disable=too-few-public-methods
    """
    Detailed view of one stopped pool.
    """

    def __init__(self, uuid_formatter, selection):
        """
        Initializer.
        :param uuid_formatter: function to format a UUID str or UUID
        :param uuid_formatter: str or UUID -> str
        :param PoolId selection: how to select pools to list
        """
        self.uuid_formatter = uuid_formatter
        self.selection = selection

    def _print_detail_view(self, pool_uuid, pool):
        """
        Print detailed view of a stopped pool.

        :param str pool_uuid: the pool UUID
        :param StoppedPool pool: information about a single pool
        :type pool: dict of str * object
        """
        print(f"UUID: {self.uuid_formatter(pool_uuid)}")

        print(f"Name: {self._pool_name(pool.name)}")

        print(f"Metadata Version: {self._metadata_version_str(pool.metadata_version)}")

        if pool.metadata_version is MetadataVersion.V1:  # pragma: no cover
            key_description = pool.key_description
            clevis_info = pool.clevis_info

            if clevis_info is None and key_description is None:
                print("Encryption Enabled: No")
            else:
                print("Encryption Enabled: Yes")

                key_description_str = _non_existent_or_inconsistent_to_str(
                    key_description
                )
                print(f"    Key Description: {key_description_str}")

                clevis_info_str = _non_existent_or_inconsistent_to_str(
                    clevis_info,
                    interp=_clevis_to_str,
                )
                print(f"    Clevis Configuration: {clevis_info_str}")

        elif pool.metadata_version is MetadataVersion.V2:
            # This condition only happens when pool metadata is not available
            if pool.features is None:  # pragma: no cover
                print("Encryption Enabled: Unknown")

            elif PoolFeature.ENCRYPTION in pool.features:
                print("Encryption Enabled: Yes")
                print(
                    "    Allows Unlock via a Key in Kernel Keyring or "
                    "a User-Entered Passphrase: "
                    f'{"Yes" if PoolFeature.KEY_DESCRIPTION_PRESENT in pool.features else "No"}'
                )
                print(
                    "    Allows Unattended Unlock via Clevis: "
                    f'{"Yes" if PoolFeature.CLEVIS_PRESENT in pool.features else "No"}'
                )
            else:
                print("Encryption Enabled: No")

        else:  # pragma: no cover
            print("Encryption Enabled: <UNAVAILABLE>")

        print("Devices:")
        for dev in pool.devs:
            print(f"{self.uuid_formatter(dev.uuid)}  {dev.devnode}")

    def display(self):
        """
        Display info about a stopped pool.
        """

        proxy = get_object(TOP_OBJECT)
        stopped_pools = fetch_stopped_pools_property(proxy)
        selection_func = self.selection.stopped_pools_func()

        stopped_pool = next(
            (
                (uuid, info)
                for (uuid, info) in stopped_pools.items()
                if selection_func(uuid, info)
            ),
            None,
        )

        if stopped_pool is None:
            raise StratisCliResourceNotFoundError("list", str(self.selection))

        (pool_uuid, pool) = stopped_pool

        self._print_detail_view(pool_uuid, StoppedPool(pool))


class StoppedTable(Stopped):  # pylint: disable=too-few-public-methods
    """
    Table view of one or many stopped pools.
    """

    def __init__(self, uuid_formatter):
        """
        Initializer.
        :param uuid_formatter: function to format a UUID str or UUID
        :param uuid_formatter: str or UUID -> str
        """
        self.uuid_formatter = uuid_formatter

    def display(self):
        """
        List stopped pools.
        """
        proxy = get_object(TOP_OBJECT)

        stopped_pools = fetch_stopped_pools_property(proxy)

        def clevis_str(value, metadata_version, features):
            if metadata_version is MetadataVersion.V2:
                return (
                    "<UNKNOWN>"
                    if features is None
                    else (
                        (
                            "<PRESENT>"
                            if PoolFeature.CLEVIS_PRESENT in features
                            else "N/A"
                        )
                        if PoolFeature.ENCRYPTION in features
                        else "<UNENCRYPTED>"
                    )
                )

            if value is None:  # pragma: no cover
                return "<UNENCRYPTED>"

            return _non_existent_or_inconsistent_to_str(
                value,
                interp=lambda _: "present",
            )  # pragma: no cover

        def key_description_str(value, metadata_version, features):
            if metadata_version is MetadataVersion.V2:
                return (
                    "<UNKNOWN>"
                    if features is None
                    else (
                        (
                            "<PRESENT>"
                            if PoolFeature.KEY_DESCRIPTION_PRESENT in features
                            else "N/A"
                        )
                        if PoolFeature.ENCRYPTION in features
                        else "<UNENCRYPTED>"
                    )
                )

            if value is None:  # pragma: no cover
                return "<UNENCRYPTED>"

            return _non_existent_or_inconsistent_to_str(value)  # pragma: no cover

        tables = [
            (
                self._pool_name(sp.name),
                self._metadata_version_str(sp.metadata_version),
                self.uuid_formatter(pool_uuid),
                str(len(sp.devs)),
                key_description_str(
                    sp.key_description, sp.metadata_version, sp.features
                ),
                clevis_str(sp.clevis_info, sp.metadata_version, sp.features),
            )
            for pool_uuid, sp in (
                (pool_uuid, StoppedPool(info))
                for pool_uuid, info in stopped_pools.items()
            )
        ]

        print_table(
            ["Name", "Version", "UUID", "# Devices", "Key Description", "Clevis"],
            sorted(tables, key=lambda entry: entry[0]),
            ["<", ">", "<", ">", "<", "<"],
        )
