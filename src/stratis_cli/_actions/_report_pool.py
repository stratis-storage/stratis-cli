# Copyright 2023 Red Hat, Inc.
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
Pool report.
"""

# isort: STDLIB
import subprocess
from abc import ABC, abstractmethod

# isort: THIRDPARTY
import dbus

from .._errors import StratisCliResourceNotFoundError
from .._stratisd_constants import PoolIdType
from ._connection import get_object
from ._constants import TOP_OBJECT


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


def report_pool(uuid_formatter, selection, *, stopped=False):
    """
    List the specified information about pools.
    """
    klass = (
        Stopped(uuid_formatter, selection)
        if stopped
        else Default(uuid_formatter, selection)
    )
    klass.report_pool()


class Report(ABC):  # pylint: disable=too-few-public-methods
    """
    Handle reporting on a pool or pools.
    """

    def __init__(self, uuid_formatter, selection):
        """
        Initialize a List object.
        :param uuid_formatter: function to format a UUID str or UUID
        :param uuid_formatter: str or UUID -> str
        :param selection: how to select the pool to display
        :type selection: pair of str * object
        """
        self.uuid_formatter = uuid_formatter
        self.selection = selection

    @abstractmethod
    def report_pool(self):
        """
        List the pools.
        """


class Default(Report):  # pylint: disable=too-few-public-methods
    """
    Report on pools that stratis list by default.
    """

    def report_pool(self):
        """
        Do pool reports.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MODev, ObjectManager, devs, pools

        proxy = get_object(TOP_OBJECT)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (selection_type, selection_value) = self.selection
        (selection_key, selection_value) = (
            ("Uuid", selection_value.hex)
            if selection_type == PoolIdType.UUID
            else ("Name", selection_value)
        )

        (pool_object_path, _) = next(
            pools(props={selection_key: selection_value})
            .require_unique_match(True)
            .search(managed_objects)
        )

        modevs = (
            MODev(info)
            for objpath, info in devs(props={"Pool": pool_object_path}).search(
                managed_objects
            )
        )

        blkdevs = [dev.Devnode() for dev in modevs]
        # Ignore bandit B603 errors.  Input comes from D-Bus and has
        # been processed.
        subprocess.run(["/usr/bin/lsblk", "-i"] + blkdevs, check=True)  # nosec B603


class Stopped(Report):  # pylint: disable=too-few-public-methods
    """
    Support for reporting on stopped pools.
    """

    def report_pool(self):
        """
        Report on stopped pool.
        """
        proxy = get_object(TOP_OBJECT)

        stopped_pools = _fetch_stopped_pools_property(proxy)

        (selection_type, selection_value) = self.selection

        if selection_type == PoolIdType.UUID:
            selection_value = selection_value.hex

            def selection_func(uuid, _info):
                return uuid == selection_value

        else:

            def selection_func(_uuid, info):
                return info.get("name") == selection_value

        stopped_pool = next(
            (
                info
                for (uuid, info) in stopped_pools.items()
                if selection_func(uuid, info)
            ),
            None,
        )

        if stopped_pool is None:
            raise StratisCliResourceNotFoundError("list", selection_value)

        # Ignore bandit B603 errors.  Input comes from D-Bus and has
        # been processed.
        blkdevs = [dev[dbus.String("devnode")] for dev in stopped_pool["devs"]]
        subprocess.run(["/usr/bin/lsblk", "-i"] + blkdevs, check=True)  # nosec B603
