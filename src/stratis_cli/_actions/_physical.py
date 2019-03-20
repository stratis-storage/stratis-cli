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

from .._stratisd_constants import BLOCK_DEV_STATE_TO_NAME
from .._stratisd_constants import BLOCK_DEV_TIER_TO_NAME

from ._connection import get_object
from ._constants import SECTOR_SIZE
from ._constants import TOP_OBJECT
from ._data import devs
from ._data import MODev
from ._data import ObjectManager
from ._formatting import print_table
from ._util import bytes_to_human, get_objects


class PhysicalActions():
    """
    Actions on the physical aspects of a pool.
    """
    # pylint: disable=too-few-public-methods

    @staticmethod
    def list_pool(namespace):
        """
        List devices. If a pool is specified in the namespace, list devices
        for that pool. Otherwise, list all devices for all pools.
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (modevs, path_to_name) = get_objects(namespace, "pool_name",
                                             managed_objects, devs, MODev)

        tables = [[
            path_to_name[modev.Pool()],
            modev.Devnode(),
            bytes_to_human(int(modev.TotalPhysicalSize()) * SECTOR_SIZE),
            BLOCK_DEV_STATE_TO_NAME(modev.State(), True),
            BLOCK_DEV_TIER_TO_NAME(modev.Tier(), True)
        ] for modev in modevs]
        print_table(
            ["Pool Name", "Device Node", "Physical Size", "State", "Tier"],
            sorted(tables, key=lambda entry: (entry[0], entry[1])),
            ['<', '<', '>', '>', '>'])
