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
Miscellaneous debugging actions.
"""

# isort: STDLIB
import os

from .._errors import StratisCliEngineError, StratisCliSynthUeventError
from .._stratisd_constants import StratisdErrors
from ._connection import get_object
from ._constants import TOP_OBJECT


class TopDebugActions:  # pylint: disable=too-few-public-methods
    """
    Top level object debug actions.
    """

    @staticmethod
    def refresh_state(_namespace):
        """
        Refresh pools from their metadata up.
        """
        from ._data import Manager  # pylint: disable=import-outside-toplevel

        (return_code, message) = Manager.Methods.RefreshState(
            get_object(TOP_OBJECT), {}
        )
        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

    @staticmethod
    def send_uevent(namespace):
        """
        Issue a synthetic uevent from the CLI.
        """
        try:
            realdevice = os.path.realpath(namespace.device, strict=True)
            sysfs_device_uevent = (
                realdevice.replace("/dev/", "/sys/class/block/") + "/uevent"
            )  # pragma: no cover

            with open(
                sysfs_device_uevent, "w", encoding="utf-8"
            ) as uevent_file:  # pragma: no cover
                uevent_file.write("change")
        except Exception as err:
            raise StratisCliSynthUeventError(
                f"Failed to send synth event: {err}"
            ) from err


class PoolDebugActions:  # pylint: disable=too-few-public-methods
    """
    Pool debug actions.
    """

    @staticmethod
    def get_object_path(namespace):
        """
        Get object path corresponding to a pool.

        :raises StratisCliEngineError:
        """

        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        maybe_pool_name_opt = getattr(namespace, "name", None)
        props = (
            {"Uuid": namespace.uuid.hex}
            if maybe_pool_name_opt is None
            else {"Name": maybe_pool_name_opt}
        )
        (pool_object_path, _) = next(
            pools(props=props).require_unique_match(True).search(managed_objects)
        )
        print(pool_object_path)


class FilesystemDebugActions:  # pylint: disable=too-few-public-methods
    """
    Filesystem debug actions.
    """

    @staticmethod
    def get_object_path(namespace):
        """
        Get object path corresponding to a pool.

        :raises StratisCliEngineError:
        """

        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, filesystems

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        maybe_fs_name_opt = getattr(namespace, "name", None)
        props = (
            {"Uuid": namespace.uuid.hex}
            if maybe_fs_name_opt is None
            else {"Name": maybe_fs_name_opt}
        )
        (fs_object_path, _) = next(
            filesystems(props=props).require_unique_match(True).search(managed_objects)
        )
        print(fs_object_path)


class BlockdevDebugActions:  # pylint: disable=too-few-public-methods
    """
    Blockdev debug actions.
    """

    @staticmethod
    def get_object_path(namespace):
        """
        Get object path corresponding to a pool.

        :raises StratisCliEngineError:
        """

        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, devs

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        props = {"Uuid": namespace.uuid.hex}

        (blockdev_object_path, _) = next(
            devs(props=props).require_unique_match(True).search(managed_objects)
        )
        print(blockdev_object_path)
