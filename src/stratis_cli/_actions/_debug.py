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
import json
import os

from .._constants import FilesystemId, PoolId
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
            realdevice = os.path.realpath(namespace.device)
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
        pool_id = PoolId.from_parser_namespace(namespace)
        assert pool_id is not None
        (pool_object_path, _) = next(
            pools(props=pool_id.managed_objects_key())
            .require_unique_match(True)
            .search(managed_objects)
        )
        print(pool_object_path)

    @staticmethod
    def get_metadata(namespace):
        """
        Get some information about the pool-level metadata.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        pool_id = PoolId.from_parser_namespace(namespace)
        assert pool_id is not None
        (pool_object_path, _) = next(
            pools(props=pool_id.managed_objects_key())
            .require_unique_match(True)
            .search(managed_objects)
        )

        (metadata, return_code, message) = Pool.Methods.Metadata(
            get_object(pool_object_path), {"current": not namespace.written}
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if namespace.pretty:
            print(json.dumps(json.loads(metadata), sort_keys=True, indent=4))
        else:
            print(json.dumps(json.loads(metadata)))


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
        fs_id = FilesystemId.from_parser_namespace(namespace)
        assert fs_id is not None
        (fs_object_path, _) = next(
            filesystems(props=fs_id.managed_objects_key())
            .require_unique_match(True)
            .search(managed_objects)
        )
        print(fs_object_path)

    @staticmethod
    def get_metadata(namespace):
        """
        Get filesystem medatada. If a specific filesystem is not specified,
        get metadata for all filesystems in the pool.

        :raises StratisCliEngineError:
        """

        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        (metadata, return_code, message) = Pool.Methods.FilesystemMetadata(
            get_object(pool_object_path),
            {
                "fs_name": (
                    (False, "")
                    if namespace.fs_name is None
                    else (True, namespace.fs_name)
                ),
                "current": not namespace.written,
            },
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if namespace.pretty:
            print(json.dumps(json.loads(metadata), sort_keys=True, indent=4))
        else:
            print(json.dumps(json.loads(metadata)))


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
