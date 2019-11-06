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

from justbytes import Range

from .._stratisd_constants import BLOCK_DEV_TIER_TO_NAME

from ._connection import get_object
from ._constants import BLOCKDEV_INTERFACE
from ._constants import TOP_OBJECT
from ._formatting import TABLE_FAILURE_STRING
from ._formatting import fetch_property
from ._formatting import print_table


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
        from ._data import devs
        from ._data import pools
        from ._data import FetchProperties
        from ._data import MODev
        from ._data import MOPool
        from ._data import ObjectManager

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
            physical_size = fetch_property(
                BLOCKDEV_INTERFACE, props, "TotalPhysicalSize", Range
            )
            return TABLE_FAILURE_STRING if physical_size is None else str(physical_size)

        tables = [
            [
                path_to_name[modev.Pool()],
                modev.Devnode(),
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
