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
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
)
from uuid import UUID

# isort: THIRDPARTY
from dateutil import parser as date_parser
from justbytes import Range

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientMissingPropertyError

from .._alerts import (
    PoolAllocSpaceAlert,
    PoolDeviceSizeChangeAlert,
    PoolEncryptionAlert,
    PoolMaintenanceAlert,
)
from .._constants import PoolId
from .._errors import StratisCliResourceNotFoundError
from .._stratisd_constants import ClevisInfo, MetadataVersion, PoolActionAvailability
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import (
    TABLE_UNKNOWN_STRING,
    TOTAL_USED_FREE,
    get_property,
    print_table,
)
from ._utils import (
    EncryptionInfo,
    EncryptionInfoClevis,
    EncryptionInfoKeyDescription,
    PoolFeature,
    SizeTriple,
    StoppedPool,
    fetch_stopped_pools_property,
)


# This method is only used with legacy pools
def _non_existent_or_inconsistent_to_str(
    value: EncryptionInfo | None,
    *,
    inconsistent_str: str = "inconsistent",
    non_existent_str: str = "N/A",
    interp: Callable[[Any], str] = str,
) -> str:  # pragma: no cover
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
    if value is None:
        return non_existent_str

    if not value.consistent():
        return inconsistent_str

    inner_value = value.value

    if inner_value is None:
        return non_existent_str

    return interp(inner_value)


class TokenSlotInfo:
    """
    Just a class to merge info about two different ways of occupying LUKS
    token slots into one, so that the two different ways can be sorted by
    token and then printed.
    """

    def __init__(
        self,
        token_slot: int,
        *,
        key: str | None = None,
        clevis: tuple[str, Any] | None = None,
    ):
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

    def __str__(self) -> str:
        return f"Token Slot: {self.token_slot}{os.linesep}" + (
            f"    Key Description: {self.key}"
            if self.clevis is None
            else (
                f"    Clevis Pin: {self.clevis[0]}{os.linesep}"
                f"    Clevis Configuration: {self.clevis[1]}"
            )
        )


class DeviceSizeChangedAlerts:
    """
    Calculate alerts for changed devices; requires searching among devices.
    """

    def __init__(
        self, devs_to_search: Iterable[tuple[Any, Mapping[str, Mapping[str, Any]]]]
    ):
        """
        Initializer.
        """
        from ._data import MODev  # noqa: PLC0415

        (increased, decreased) = (set(), set())
        for _, info in devs_to_search:
            modev = MODev(info)
            size = Range(modev.TotalPhysicalSize())
            observed_size = get_property(modev.NewPhysicalSize(), Range, size)
            if observed_size > size:  # pragma: no cover
                increased.add(modev.Pool())
            if observed_size < size:  # pragma: no cover
                decreased.add(modev.Pool())

        (self.increased, self.decreased) = (increased, decreased)

    def alert_codes(self, pool_object_path: str) -> list[PoolDeviceSizeChangeAlert]:
        """
        Get the code from sets and one pool object path.

        :param pool_object_path: the pool object path
        :returns: the codes
        """
        if (
            pool_object_path in self.increased and pool_object_path in self.decreased
        ):  # pragma: no cover
            return [
                PoolDeviceSizeChangeAlert.DEVICE_SIZE_INCREASED,
                PoolDeviceSizeChangeAlert.DEVICE_SIZE_DECREASED,
            ]
        if pool_object_path in self.increased:  # pragma: no cover
            return [PoolDeviceSizeChangeAlert.DEVICE_SIZE_INCREASED]
        if pool_object_path in self.decreased:  # pragma: no cover
            return [PoolDeviceSizeChangeAlert.DEVICE_SIZE_DECREASED]
        return []


def list_pools(
    uuid_formatter: Callable[[str | UUID], str],
    *,
    stopped: bool = False,
    selection: PoolId | None = None,
):
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
    else:  # noqa: PLR5501
        if selection is None:
            klass = DefaultTable(uuid_formatter)
        else:
            klass = DefaultDetail(uuid_formatter, selection)

    klass.display()


def _clevis_to_str(clevis_info: ClevisInfo) -> str:  # pragma: no cover
    """
    :param ClevisInfo clevis_info: the Clevis info to stringify
    :return: a string that represents the clevis info
    :rtype: str
    """

    config_string = " ".join(
        f"{key}: {value}" for key, value in clevis_info.config.items()
    )
    return f"{clevis_info.pin}   {config_string}"


class ListPool(ABC):
    """
    Handle listing a pool or pools.
    """

    @abstractmethod
    def display(self):
        """
        List the pools.
        """

    def __init__(self, uuid_formatter: Callable[[UUID | str], str]):
        """
        Initializer.
        """
        self.uuid_formatter = uuid_formatter


class Default(ListPool):
    """
    Handle listing the pools that are listed by default.
    """

    @staticmethod
    def metadata_version(mopool: Any) -> MetadataVersion | None:
        """
        Return the metadata version, dealing with the possibility that it
        might be unparsable.
        """
        try:
            return MetadataVersion(int(mopool.MetadataVersion()))
        except ValueError:  # pragma: no cover
            return None
        except DbusClientMissingPropertyError:
            return None

    @staticmethod
    def _volume_key_loaded(mopool: Any) -> tuple[bool, bool | str]:
        """
        The string result is an error message indicating that the volume key
        state is unknown.
        """
        result = mopool.VolumeKeyLoaded()
        if isinstance(result, int):
            return (True, bool(result))
        return (False, str(result))  # pragma: no cover

    @staticmethod
    def alert_codes(
        mopool: Any,
    ) -> list[PoolEncryptionAlert | PoolAllocSpaceAlert | PoolMaintenanceAlert]:
        """
        Return alert code objects for a pool. If some D-Bus properties are
        missing, the information related to those D-Bus properties is simply
        omitted.

        :param mopool: object to access pool properties

        :returns: list of alerts obtainable from GetManagedObjects properties
        """
        try:
            action_availability = PoolActionAvailability[str(mopool.AvailableActions())]
            availability_alerts = action_availability.pool_maintenance_alerts()

        except DbusClientMissingPropertyError:
            availability_alerts = []

        try:
            no_alloc_space_alerts = (
                [PoolAllocSpaceAlert.NO_ALLOC_SPACE] if mopool.NoAllocSpace() else []
            )
        except DbusClientMissingPropertyError:
            no_alloc_space_alerts = []

        metadata_version = Default.metadata_version(mopool)

        try:
            (vkl_is_bool, volume_key_loaded) = Default._volume_key_loaded(mopool)
            encrypted = bool(mopool.Encrypted())
            pool_encryption_alerts: list[PoolEncryptionAlert] = (
                [PoolEncryptionAlert.VOLUME_KEY_NOT_LOADED]
                if metadata_version is MetadataVersion.V2
                and encrypted
                and vkl_is_bool
                and not volume_key_loaded
                else []
            ) + (
                [PoolEncryptionAlert.VOLUME_KEY_STATUS_UNKNOWN]
                if metadata_version is MetadataVersion.V2
                and encrypted
                and not vkl_is_bool
                else []
            )
        except DbusClientMissingPropertyError:
            pool_encryption_alerts = [PoolEncryptionAlert.VOLUME_KEY_STATUS_UNKNOWN]
        return availability_alerts + no_alloc_space_alerts + pool_encryption_alerts

    @staticmethod
    def size_triple(mopool: Any) -> SizeTriple:
        """
        Calculate SizeTriple from size information.
        """
        try:
            size = Range(mopool.TotalPhysicalSize())
        except DbusClientMissingPropertyError:
            size = None

        try:
            used = get_property(mopool.TotalPhysicalUsed(), Range, None)
        except DbusClientMissingPropertyError:
            used = None

        return SizeTriple(size, used)

    def uuid_str(self, mopool: Any) -> str:
        """
        Return a string representation of UUID, correctly formatted.
        """
        try:
            return self.uuid_formatter(mopool.Uuid())
        except DbusClientMissingPropertyError:
            return TABLE_UNKNOWN_STRING

    @staticmethod
    def name_str(mopool: Any) -> str:
        """
        Return a string representation of the pool name.
        """
        try:
            return mopool.Name()
        except DbusClientMissingPropertyError:
            return TABLE_UNKNOWN_STRING


class DefaultDetail(Default):
    """
    List one pool with a detail view.
    """

    def __init__(self, uuid_formatter: Callable[[str | UUID], str], selection: PoolId):
        """
        Initializer.
        :param uuid_formatter: function to format a UUID str or UUID
        :param uuid_formatter: str or UUID -> str
        :param PoolId selection: how to select pools to list
        """
        super().__init__(uuid_formatter)
        self.selection = selection

    def _print_detail_view(  # noqa: PLR0912,PLR0915
        self, pool_object_path: str, mopool: Any, alerts: DeviceSizeChangedAlerts
    ):
        """
        Print the detailed view for a single pool.

        :param UUID uuid: the pool uuid
        :param pool_object_path: object path of the pool
        :param MOPool mopool: properties of the pool
        :param DeviceSizeChangedAlerts alerts: pool alerts
        """
        print(f"UUID: {self.uuid_str(mopool)}")
        print(f"Name: {Default.name_str(mopool)}")

        alert_summary = sorted(
            f"{code}: {code.summarize()}"
            for code in alerts.alert_codes(pool_object_path)
            + Default.alert_codes(mopool)
        )
        print(f"Alerts: {len(alert_summary)}")
        for line in alert_summary:
            print(f"     {line}")

        metadata_version = Default.metadata_version(mopool)
        metadata_version_str = (
            metadata_version if metadata_version is not None else TABLE_UNKNOWN_STRING
        )
        print(f"Metadata Version: {metadata_version_str}")

        try:
            actions_allowed_str = PoolActionAvailability[
                str(mopool.AvailableActions())
            ].name
        except DbusClientMissingPropertyError:
            actions_allowed_str = TABLE_UNKNOWN_STRING
        print(f"Actions Allowed: {actions_allowed_str}")

        try:
            cache_str = "Yes" if mopool.HasCache() else "No"
        except DbusClientMissingPropertyError:
            cache_str = TABLE_UNKNOWN_STRING
        print(f"Cache: {cache_str}")

        try:
            fs_limit_str = mopool.FsLimit()
        except DbusClientMissingPropertyError:
            fs_limit_str = TABLE_UNKNOWN_STRING
        print(f"Filesystem Limit: {fs_limit_str}")

        try:
            allow_overprovisioning_str = "Yes" if mopool.Overprovisioning() else "No"
        except DbusClientMissingPropertyError:
            allow_overprovisioning_str = TABLE_UNKNOWN_STRING
        print(f"Allows Overprovisioning: {allow_overprovisioning_str}")

        try:
            encrypted = bool(mopool.Encrypted())
        except DbusClientMissingPropertyError:
            encrypted = None

        if encrypted is None:
            print(f"Encryption Enabled: {TABLE_UNKNOWN_STRING}")
        elif encrypted is True:
            print("Encryption Enabled: Yes")

            try:
                reencrypted = get_property(
                    mopool.LastReencryptedTimestamp(),
                    lambda t: date_parser.isoparse(t)
                    .astimezone()
                    .strftime("%b %d %Y %H:%M"),
                    "Never",
                )
            except DbusClientMissingPropertyError:
                reencrypted = TABLE_UNKNOWN_STRING
            print(f"    Last Time Reencrypted: {reencrypted}")

            if metadata_version is MetadataVersion.V1:  # pragma: no cover
                try:
                    key_description_str = _non_existent_or_inconsistent_to_str(
                        EncryptionInfoKeyDescription(mopool.KeyDescriptions())
                    )
                except DbusClientMissingPropertyError:
                    key_description_str = TABLE_UNKNOWN_STRING
                print(f"    Key Description: {key_description_str}")

                try:
                    clevis_info_str = _non_existent_or_inconsistent_to_str(
                        EncryptionInfoClevis(mopool.ClevisInfos()),
                        interp=_clevis_to_str,
                    )
                except DbusClientMissingPropertyError:
                    clevis_info_str = TABLE_UNKNOWN_STRING
                print(f"    Clevis Configuration: {clevis_info_str}")
            elif metadata_version is MetadataVersion.V2:

                try:
                    free_str = get_property(
                        mopool.FreeTokenSlots(),
                        lambda x: str(int(x)),
                        TABLE_UNKNOWN_STRING,
                    )
                except DbusClientMissingPropertyError:
                    free_str = TABLE_UNKNOWN_STRING
                print(f"    Free Token Slots Remaining: {free_str}")

                try:
                    key_encryption_infos = [
                        TokenSlotInfo(token_slot, key=str(description))
                        for token_slot, description in mopool.KeyDescriptions()
                    ]
                except DbusClientMissingPropertyError:
                    key_encryption_infos = []

                try:
                    clevis_encryption_infos = [
                        TokenSlotInfo(
                            token_slot, clevis=(str(pin), json.loads(str(config)))
                        )
                        for token_slot, (pin, config) in mopool.ClevisInfos()
                    ]
                except DbusClientMissingPropertyError:
                    clevis_encryption_infos = []

                encryption_infos = sorted(
                    key_encryption_infos + clevis_encryption_infos,
                    key=lambda x: x.token_slot,
                )
                if encryption_infos == []:  # pragma: no cover
                    print("    No token slot information available")
                else:
                    for info in encryption_infos:
                        for line in str(info).split(os.linesep):
                            print(f"    {line}")
        else:
            print("Encryption Enabled: No")

        size_triple = Default.size_triple(mopool)

        def size_str(value: Range | None) -> str:
            return TABLE_UNKNOWN_STRING if value is None else str(value)

        try:
            fully_allocated_str = "Yes" if mopool.NoAllocSpace() else "No"
        except DbusClientMissingPropertyError:
            fully_allocated_str = TABLE_UNKNOWN_STRING
        print(f"Fully Allocated: {fully_allocated_str}")

        print(f"    Size: {size_str(size_triple.total())}")

        try:
            allocated_size = Range(mopool.AllocatedSize())
        except DbusClientMissingPropertyError:
            allocated_size = None
        print(f"    Allocated: {size_str(allocated_size)}")
        print(f"    Used: {size_str(size_triple.used())}")

    def display(self):
        """
        List a single pool in detail.
        """
        from ._data import MOPool, ObjectManager, devs, pools  # noqa: PLC0415

        proxy = get_object(TOP_OBJECT)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, mopool) = next(
            pools(props=self.selection.managed_objects_key())
            .require_unique_match(True)
            .search(managed_objects)
        )

        alerts = DeviceSizeChangedAlerts(
            devs(props={"Pool": pool_object_path}).search(managed_objects)
        )

        self._print_detail_view(pool_object_path, MOPool(mopool), alerts)


class DefaultTable(Default):
    """
    List several pools with a table view.
    """

    def display(self):
        """
        List pools in table view.
        """
        from ._data import MOPool, ObjectManager, devs, pools  # noqa: PLC0415

        proxy = get_object(TOP_OBJECT)

        def physical_size_triple(mopool: Any) -> str:
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
            size_triple = Default.size_triple(mopool)

            return " / ".join(
                (
                    TABLE_UNKNOWN_STRING if x is None else str(x)
                    for x in (
                        size_triple.total(),
                        size_triple.used(),
                        size_triple.free(),
                    )
                )
            )

        def properties_string(mopool: Any) -> str:
            """
            Make a string encoding some important properties of the pool

            :param mopool: an object representing all the properties of the pool
            :type mopool: MOPool
            :param props_map: a map of properties returned by GetAllProperties
            :type props_map: dict of str * any
            """

            def gen_string(has_property: bool | None, code: str) -> str:
                """
                Generate the display string for a boolean property

                :param bool has_property: whether the property is true or false
                :param str code: the code to generate the string for
                :returns: the generated string
                :rtype: str
                """
                return (
                    "?"
                    if has_property is None
                    else (" " if has_property else "~") + code
                )

            metadata_version = Default.metadata_version(mopool)

            try:
                has_cache = bool(mopool.HasCache())
            except DbusClientMissingPropertyError:
                has_cache = None

            try:
                encrypted = bool(mopool.Encrypted())
            except DbusClientMissingPropertyError:
                encrypted = None

            try:
                overprovisioning = bool(mopool.Overprovisioning())
            except DbusClientMissingPropertyError:
                overprovisioning = None

            props_list = [
                (
                    (
                        None
                        if metadata_version is None
                        else metadata_version is MetadataVersion.V1
                    ),
                    "Le",
                ),
                (has_cache, "Ca"),
                (encrypted, "Cr"),
                (overprovisioning, "Op"),
            ]
            return ",".join(gen_string(x, y) for x, y in props_list)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        alerts = DeviceSizeChangedAlerts(devs().search(managed_objects))

        pools_with_props = [
            (objpath, MOPool(info)) for objpath, info in pools().search(managed_objects)
        ]

        def alerts_str(mopool: Any, pool_object_path: str) -> str:
            return ", ".join(
                sorted(
                    str(code)
                    for code in (
                        Default.alert_codes(mopool)
                        + alerts.alert_codes(pool_object_path)
                    )
                )
            )

        tables = [
            (
                Default.name_str(mopool),
                physical_size_triple(mopool),
                properties_string(mopool),
                self.uuid_str(mopool),
                alerts_str(mopool, pool_object_path),
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


class Stopped(ListPool):
    """
    Support for listing stopped pools.
    """

    @staticmethod
    def _pool_name(maybe_value: str | None) -> str:
        """
        Return formatted string for pool name.

        :param maybe_value: the pool name
        :type maybe_value: str or NoneType
        """
        return "<UNAVAILABLE>" if maybe_value is None else maybe_value

    @staticmethod
    def _metadata_version_str(maybe_value: MetadataVersion | None) -> str:
        """
        Return formatted string for metadata version.

        :param maybe_value: the metadata version
        :type maybe_value: int or NoneType
        """
        return "<MIXED>" if maybe_value is None else str(maybe_value)


class StoppedDetail(Stopped):
    """
    Detailed view of one stopped pool.
    """

    def __init__(self, uuid_formatter: Callable[[str | UUID], str], selection: PoolId):
        """
        Initializer.
        :param uuid_formatter: function to format a UUID str or UUID
        :param uuid_formatter: str or UUID -> str
        :param PoolId selection: how to select pools to list
        """
        super().__init__(uuid_formatter)
        self.selection = selection

    def _print_detail_view(self, pool_uuid: str, pool: StoppedPool):
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


class StoppedTable(Stopped):
    """
    Table view of one or many stopped pools.
    """

    def display(self):
        """
        List stopped pools.
        """
        proxy = get_object(TOP_OBJECT)

        stopped_pools = fetch_stopped_pools_property(proxy)

        def clevis_str(
            value: Any | None,
            metadata_version: MetadataVersion | None,
            features: frozenset[PoolFeature] | None,
        ) -> str:
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

        def key_description_str(
            value: EncryptionInfoKeyDescription | None,
            metadata_version: MetadataVersion | None,
            features: frozenset[PoolFeature] | None,
        ) -> str:
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
