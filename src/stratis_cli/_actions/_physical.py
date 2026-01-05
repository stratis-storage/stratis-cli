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

# isort: STDLIB
from argparse import Namespace
from typing import Any, Callable

# isort: THIRDPARTY
from justbytes import Range

from .._stratisd_constants import BlockDevTiers
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import (
    TABLE_UNKNOWN_STRING,
    catch_missing_property,
    get_property,
    get_uuid_formatter,
    print_table,
)


class PhysicalActions:
    """
    Actions on the physical aspects of a pool.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def list_devices(namespace: Namespace):  # pylint: disable=too-many-locals
        """
        List devices. If a pool is specified in the namespace, list devices
        for that pool. Otherwise, list all devices for all pools.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MODev, MOPool, ObjectManager, devs, pools

        # This method is invoked as the default for "stratis blockdev";
        # the namespace may not have a pool_name field.
        pool_name = getattr(namespace, "pool_name", None)

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        modevs = [
            MODev(info)
            for objpath, info in devs(
                props=(
                    None
                    if pool_name is None
                    else {
                        "Pool": next(
                            pools(props={"Name": pool_name})
                            .require_unique_match(True)
                            .search(managed_objects)
                        )[0]
                    }
                )
            ).search(managed_objects)
        ]

        path_to_name = dict(
            (path, MOPool(info).Name())
            for path, info in pools(
                props=None if pool_name is None else {"Name": pool_name}
            ).search(managed_objects)
        )

        def paths(modev: Any) -> str:
            """
            Return <physical_path> (<metadata_path>) if they are different,
            otherwise, just <metadata_path>.

            physical_path D-Bus Property key is PhysicalPath
            metadata_path D-Bus Property key is Devnode

            :param modev: object containing D-Bus properties
            :returns: the string to print
            :rtype: str
            """
            metadata_path = modev.Devnode()
            physical_path = modev.PhysicalPath()

            return (
                metadata_path
                if metadata_path == physical_path
                else f"{physical_path} ({metadata_path})"
            )

        def size_str(modev: Any) -> str:
            """
            Return in-use size (observed size) if they are different, otherwise
            just in-use size.
            """
            in_use_size = Range(modev.TotalPhysicalSize())
            observed_size = get_property(modev.NewPhysicalSize(), Range, in_use_size)
            return (
                f"{in_use_size}"
                if in_use_size == observed_size
                else f"{in_use_size} ({observed_size})"
            )

        def tier_str(modev: Any) -> str:
            """
            String representation of a tier.
            """
            try:
                return str(BlockDevTiers(modev.Tier()))
            except ValueError:  # pragma: no cover
                return TABLE_UNKNOWN_STRING

        format_uuid = get_uuid_formatter(namespace.unhyphenated_uuids)

        def missing_property(func: Callable[[Any], str]) -> Callable[[Any], str]:
            return catch_missing_property(func, TABLE_UNKNOWN_STRING)

        pool_name_func = missing_property(
            lambda mo: path_to_name.get(mo.Pool(), TABLE_UNKNOWN_STRING)
        )
        paths_func = missing_property(paths)
        size_func = missing_property(size_str)
        tier_func = missing_property(tier_str)
        uuid_func = missing_property(lambda modev: format_uuid(modev.Uuid()))

        tables = [
            [
                pool_name_func(modev),
                paths_func(modev),
                size_func(modev),
                tier_func(modev),
                uuid_func(modev),
            ]
            for modev in modevs
        ]
        print_table(
            ["Pool Name", "Device Node", "Physical Size", "Tier", "UUID"],
            sorted(tables, key=lambda entry: (entry[0], entry[1])),
            ["<", "<", ">", ">", "<"],
        )
