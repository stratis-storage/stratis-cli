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
Miscellaneous logical actions.
"""

from justbytes import Range
from dateutil import parser as date_parser

from .._errors import StratisCliEngineError
from .._errors import StratisCliNoChangeError
from .._errors import StratisCliPartialChangeError

from .._stratisd_constants import StratisdErrors

from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import print_table


class LogicalActions:
    """
    Actions on the logical aspects of a pool.
    """

    @staticmethod
    def create_volumes(namespace):
        """
        Create volumes in a pool.

        :raises StratisCliEngineError:
        """
        # pylint: disable=too-many-locals
        from ._data import MOFilesystem
        from ._data import ObjectManager
        from ._data import Pool
        from ._data import filesystems
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        requested_names = frozenset(namespace.fs_name)

        names = frozenset(
            MOFilesystem(info).Name()
            for (_, info) in filesystems(props={"Pool": pool_object_path}).search(
                managed_objects
            )
        )
        already_names = requested_names.intersection(names)

        if already_names != frozenset():
            raise StratisCliPartialChangeError(
                "create", requested_names.difference(already_names), already_names
            )

        (_, rc, message) = Pool.Methods.CreateFilesystems(
            get_object(pool_object_path), {"specs": namespace.fs_name}
        )

        if rc != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(rc, message)

    @staticmethod
    def list_volumes(namespace):
        """
        List the volumes in a pool.
        """
        from ._data import MOFilesystem
        from ._data import MOPool
        from ._data import ObjectManager
        from ._data import filesystems
        from ._data import pools

        # This method is invoked as the default for "stratis filesystem";
        # the namespace may not have a pool_name field.
        pool_name = getattr(namespace, "pool_name", None)

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        mofilesystems = (
            MOFilesystem(info)
            for _, info in filesystems(
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
        )

        path_to_name = dict(
            (path, MOPool(info).Name())
            for path, info in pools(
                props=None if pool_name is None else {"Name": pool_name}
            ).search(managed_objects)
        )

        tables = [
            [
                path_to_name[mofilesystem.Pool()],
                mofilesystem.Name(),
                str(Range(mofilesystem.Used())),
                date_parser.parse(mofilesystem.Created())
                .astimezone()
                .strftime("%b %d %Y %H:%M"),
                mofilesystem.Devnode(),
                mofilesystem.Uuid(),
            ]
            for mofilesystem in mofilesystems
        ]

        print_table(
            ["Pool Name", "Name", "Used", "Created", "Device", "UUID"],
            sorted(tables, key=lambda entry: entry[0]),
            ["<", "<", "<", "<", "<", "<"],
        )

    @staticmethod
    def destroy_volumes(namespace):
        """
        Destroy volumes in a pool.

        :raises StratisCliEngineError:
        """
        # pylint: disable=too-many-locals
        from ._data import MOFilesystem
        from ._data import ObjectManager
        from ._data import Pool
        from ._data import filesystems
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        requested_names = frozenset(namespace.fs_name)

        pool_filesystems = {
            MOFilesystem(info).Name(): op
            for (op, info) in filesystems(props={"Pool": pool_object_path}).search(
                managed_objects
            )
        }
        already_removed = requested_names.difference(frozenset(pool_filesystems.keys()))

        if already_removed != frozenset():
            raise StratisCliPartialChangeError(
                "destroy", requested_names.difference(already_removed), already_removed
            )

        fs_object_paths = [
            op for (name, op) in pool_filesystems if name in requested_names
        ]

        (_, rc, message) = Pool.Methods.DestroyFilesystems(
            get_object(pool_object_path), {"filesystems": fs_object_paths}
        )

        if rc != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(rc, message)

    @staticmethod
    def snapshot_filesystem(namespace):
        """
        Snapshot filesystem in a pool.

        :raises StratisCliEngineError:
        """
        from ._data import ObjectManager
        from ._data import Pool
        from ._data import filesystems
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )
        (origin_fs_object_path, _) = next(
            filesystems(props={"Name": namespace.origin_name, "Pool": pool_object_path})
            .require_unique_match(True)
            .search(managed_objects)
        )

        ((changed, _), rc, message) = Pool.Methods.SnapshotFilesystem(
            get_object(pool_object_path),
            {"origin": origin_fs_object_path, "snapshot_name": namespace.snapshot_name},
        )

        if rc != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(rc, message)

        if not changed:
            resource = namespace.snapshot_name
            raise StratisCliNoChangeError("snapshot", resource)

    @staticmethod
    def rename_fs(namespace):
        """
        Rename a filesystem.
        """
        from ._data import ObjectManager
        from ._data import Filesystem
        from ._data import filesystems
        from ._data import pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )
        (fs_object_path, _) = next(
            filesystems(props={"Name": namespace.fs_name, "Pool": pool_object_path})
            .require_unique_match(True)
            .search(managed_objects)
        )

        ((changed, _), rc, message) = Filesystem.Methods.SetName(
            get_object(fs_object_path), {"name": namespace.new_name}
        )

        if rc != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(rc, message)

        if not changed:
            resource = namespace.new_name
            raise StratisCliNoChangeError("rename", resource)
