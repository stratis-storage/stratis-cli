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

# isort: THIRDPARTY
from justbytes import Range

from .._stratisd_constants import BLOCK_DEV_TIER_TO_NAME
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import TABLE_FAILURE_STRING, get_property, print_table


class PhysicalActions:
    """
    Actions on the physical aspects of a pool.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def list_devices(namespace):
        """
        List devices. If a pool is specified in the namespace, list devices
        for that pool. Otherwise, list all devices for all pools.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import FetchProperties, MODev, MOPool, ObjectManager, devs, pools

        # This method is invoked as the default for "stratis blockdev";
        # the namespace may not have a pool_name field.
        pool_name = getattr(namespace, "pool_name", None)

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        modevs = [
            (
                FetchProperties.Methods.GetAllProperties(get_object(objpath), {}),
                MODev(info),
            )
            for objpath, info in devs(
                props=None
                if pool_name is None
                else {
                    "Pool": next(
                        pools(props={"Name": pool_name})
                        .require_unique_match(True)
                        .search(managed_objects)
                    )[0]
                }
            ).search(managed_objects)
        ]

        path_to_name = dict(
            (path, MOPool(info).Name())
            for path, info in pools(
                props=None if pool_name is None else {"Name": pool_name}
            ).search(managed_objects)
        )

        def total_physical_size(props):
            """
            Calculate the string value to display for physical size of block
            device.

            The format is just that chosen by justbytes default configuration.

            :param props: a dictionary of property values obtained
            :type props: a dict of str * object
            :returns: a string to display in the resulting list output
            :rtype: str
            """
            total_size = get_property(
                props,
                "TotalPhysicalSize",
                Range,
                TABLE_FAILURE_STRING,
            )

            total_real_size = get_property(
                props, "TotalPhysicalRealSize", Range, TABLE_FAILURE_STRING
            )

            return (
                str(total_size)
                if total_size == total_real_size
                else "%s (%s)" % (total_size, total_real_size)
            )

        def paths(modev):
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
                else "%s (%s)" % (physical_path, metadata_path)
            )

        tables = [
            [
                path_to_name[modev.Pool()],
                paths(modev),
                total_physical_size(props),
                BLOCK_DEV_TIER_TO_NAME(modev.Tier(), True),
            ]
            for (props, modev) in modevs
        ]
        print_table(
            ["Pool Name", "Device Node", "Physical Size", "Tier"],
            sorted(tables, key=lambda entry: (entry[0], entry[1])),
            ["<", "<", ">", ">"],
        )
