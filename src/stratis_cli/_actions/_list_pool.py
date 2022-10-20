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

# isort: THIRDPARTY
from justbytes import Range

from .._error_codes import PoolAllocSpaceErrorCode, PoolDeviceSizeChangeCode
from .._errors import StratisCliResourceNotFoundError
from .._stratisd_constants import PoolActionAvailability
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import (
    TABLE_FAILURE_STRING,
    TOTAL_USED_FREE,
    get_property,
    print_table,
    size_triple,
)


def _fetch_stopped_pools_property(proxy):
    """
    Fetch the StoppedPools property from stratisd.
    :param proxy: proxy to the top object in stratisd
    :return: a representation of stopped devices
    :rtype: dict
    :raises StratisCliEngineError:
    """

    # pylint: disable=import-outside-toplevel
    from ._data import Manager

    return Manager.Properties.StoppedPools.Get(proxy)


class List:
    """
    Handle listing a pool.
    """

    def __init__(self, uuid_formatter):
        """
        Initialize a List object.
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

        return List._maybe_inconsistent(value, my_func)

    @staticmethod
    def alert_string(codes):
        """
        Alert information to display, if any

        :param codes: list of error codes to display
        :type codes: list of PoolErrorCode

        :returns: string w/ alert information, "" if no alert
        :rtype: str
        """
        return ", ".join(sorted(str(code) for code in codes))

    @staticmethod
    def alert_summary(codes):
        """
        Alert summary to display, if any

        :param codes: list of error codes to display
        :type codes: list of PoolErrorCode

        :returns: string with alert summary
        :rtype: str
        """
        return [f"{str(code)}: {code.summarize()}" for code in codes]

    @staticmethod
    def alert_codes(mopool):
        """
        Return error code objects for a pool.

        :param mopool: object to access pool properties

        :returns: list of PoolErrorCode
        """
        action_availability = PoolActionAvailability.from_str(mopool.AvailableActions())
        availability_error_codes = action_availability.pool_maintenance_error_codes()

        no_alloc_space_error_codes = (
            [PoolAllocSpaceErrorCode.NO_ALLOC_SPACE] if mopool.NoAllocSpace() else []
        )

        return availability_error_codes + no_alloc_space_error_codes

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
        for (_, info) in devs_to_search:
            modev = MODev(info)
            size = Range(modev.TotalPhysicalSize())
            observed_size = get_property(modev.NewPhysicalSize(), Range, size)
            if observed_size > size:  # pragma: no cover
                increased.add(modev.Pool())
            if observed_size < size:  # pragma: no cover
                decreased.add(modev.Pool())

        return (increased, decreased)

    @staticmethod
    def _from_sets(pool_object_path, increased, decreased):
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

    def _print_detail_view(self, pool_uuid, mopool, size_change_codes):
        """
        Print the detailed view for a single pool.

        :param UUID uuid: the pool uuid
        :param MOPool mopool: properties of the pool
        :param size_change_codes: size change codes
        :type size_change_codes: list of PoolDeviceSizeChangeCode
        """
        encrypted = mopool.Encrypted()

        print(f"UUID: {self.uuid_formatter(pool_uuid)}")
        print(f"Name: {mopool.Name()}")

        alert_summary = List.alert_summary(List.alert_codes(mopool) + size_change_codes)
        print(f"Alerts: {str(len(alert_summary))}")
        for line in alert_summary:  # pragma: no cover
            print(f"     {line}")

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
            List._interp_inconsistent_option(mopool.KeyDescription())
            if encrypted
            else "unencrypted"
        )
        print(f"Key Description: {key_description_str}")

        clevis_info_str = (
            List._interp_inconsistent_option(mopool.ClevisInfo())
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

    def list_pools_default(self, *, pool_uuid=None):  # pylint: disable=too-many-locals
        """
        List all pools that are listed by default. These are all started pools.
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

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        if pool_uuid is None:
            (increased, decreased) = List._pools_with_changed_devs(
                devs().search(managed_objects)
            )

            pools_with_props = [
                (objpath, MOPool(info))
                for objpath, info in pools().search(managed_objects)
            ]

            tables = [
                (
                    mopool.Name(),
                    physical_size_triple(mopool),
                    properties_string(mopool),
                    self.uuid_formatter(mopool.Uuid()),
                    List.alert_string(
                        List.alert_codes(mopool)
                        + List._from_sets(pool_object_path, increased, decreased)
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

        else:
            this_uuid = pool_uuid.hex
            (pool_object_path, mopool) = next(
                pools(props={"Uuid": this_uuid})
                .require_unique_match(True)
                .search(managed_objects)
            )

            (increased, decreased) = List._pools_with_changed_devs(
                devs(props={"Pool": pool_object_path}).search(managed_objects)
            )

            device_change_codes = List._from_sets(
                pool_object_path, increased, decreased
            )

            self._print_detail_view(pool_uuid, MOPool(mopool), device_change_codes)

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

            return List._maybe_inconsistent(value, my_func)

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
                        info.get("key_description"), List._interp_inconsistent_option
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
                stopped_pool.get("key_description"), List._interp_inconsistent_option
            )
            print(f"Key Description: {key_description_str}")

            clevis_info_str = unencrypted_string(
                stopped_pool.get("clevis_info"), List._interp_inconsistent_option
            )
            print(f"Clevis Configuration: {clevis_info_str}")

            print("Devices:")
            for dev in stopped_pool["devs"]:
                print(f"{self.uuid_formatter(dev['uuid'])}  {dev['devnode']}")
