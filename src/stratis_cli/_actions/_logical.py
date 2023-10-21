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

# isort: THIRDPARTY
from dateutil import parser as date_parser
from justbytes import Range

from .._errors import (
    StratisCliEngineError,
    StratisCliFsSizeLimitChangeError,
    StratisCliIncoherenceError,
    StratisCliNoChangeError,
    StratisCliPartialChangeError,
)
from .._stratisd_constants import StratisdErrors
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import (
    TOTAL_USED_FREE,
    get_property,
    get_uuid_formatter,
    print_table,
    size_triple,
)


class LogicalActions:
    """
    Actions on the logical aspects of a pool.
    """

    @staticmethod
    def create_volumes(namespace):
        """
        Create volumes in a pool.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        :raises StratisCliPartialChangeError:
        """
        # pylint: disable=too-many-locals

        # pylint: disable=import-outside-toplevel
        from ._data import MOFilesystem, ObjectManager, Pool, filesystems, pools

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

        requested_size_arg = (
            (False, "")
            if namespace.size is None
            else (True, str(namespace.size.magnitude))
        )

        requested_size_limit_arg = (
            (False, "")
            if namespace.size_limit is None
            else (True, str(namespace.size_limit.magnitude))
        )

        requested_specs = [
            (n, requested_size_arg, requested_size_limit_arg) for n in requested_names
        ]

        (
            (created, list_created),
            return_code,
            message,
        ) = Pool.Methods.CreateFilesystems(
            get_object(pool_object_path), {"specs": requested_specs}
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        if not created or len(list_created) < len(requested_names):  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    f"Expected to create the specified filesystems in pool "
                    f"{namespace.pool_name} but stratisd reports that it did "
                    f"not actually create some or all of the filesystems "
                    f"requested"
                )
            )

    @staticmethod
    def list_volumes(namespace):
        """
        List the volumes in a pool.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MOFilesystem, MOPool, ObjectManager, filesystems, pools

        # This method is invoked as the default for "stratis filesystem";
        # the namespace may not have a pool_name field.
        pool_name = getattr(namespace, "pool_name", None)

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        filesystems_with_props = [
            MOFilesystem(info)
            for objpath, info in filesystems(
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

        def filesystem_size_quartet(dbus_props):
            """
            Calculate the triple to display for filesystem size.

            :param dbus_props: filesystem D-Bus properties
            :type dbus_props: MOFilesystem

            :returns: a string a formatted string showing all three values
            :rtype: str
            """
            total = Range(dbus_props.Size())
            used = get_property(dbus_props.Used(), Range, None)
            limit = get_property(dbus_props.SizeLimit(), Range, None)
            return f'{size_triple(total, used)} / {"None" if limit is None else limit}'

        format_uuid = get_uuid_formatter(namespace.unhyphenated_uuids)

        tables = [
            (
                path_to_name[mofilesystem.Pool()],
                mofilesystem.Name(),
                filesystem_size_quartet(mofilesystem),
                date_parser.parse(mofilesystem.Created())
                .astimezone()
                .strftime("%b %d %Y %H:%M"),
                mofilesystem.Devnode(),
                format_uuid(mofilesystem.Uuid()),
            )
            for mofilesystem in filesystems_with_props
        ]

        print_table(
            [
                "Pool",
                "Filesystem",
                f"{TOTAL_USED_FREE} / Limit",
                "Created",
                "Device",
                "UUID",
            ],
            sorted(tables, key=lambda entry: (entry[0], entry[1])),
            ["<", "<", "<", "<", "<", "<"],
        )

    @staticmethod
    def destroy_volumes(namespace):
        """
        Destroy volumes in a pool.

        :raises StratisCliEngineError:
        :raises StratisCliIncoherenceError:
        :raises StratisCliPartialChangeError:
        """
        # pylint: disable=too-many-locals

        # pylint: disable=import-outside-toplevel
        from ._data import MOFilesystem, ObjectManager, Pool, filesystems, pools

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
            op for (name, op) in pool_filesystems.items() if name in requested_names
        ]

        (
            (destroyed, list_destroyed),
            return_code,
            message,
        ) = Pool.Methods.DestroyFilesystems(
            get_object(pool_object_path), {"filesystems": fs_object_paths}
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if not destroyed or len(list_destroyed) < len(
            fs_object_paths
        ):  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    f"Expected to destroy the specified filesystems in pool "
                    f"{namespace.pool_name} but stratisd reports that it did "
                    f"not actually destroy some or all of the filesystems "
                    f"requested"
                )
            )

    @staticmethod
    def snapshot_filesystem(namespace):
        """
        Snapshot filesystem in a pool.

        :raises StratisCliEngineError:
        :raises StratisCliNoChangeError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, filesystems, pools

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

        ((changed, _), return_code, message) = Pool.Methods.SnapshotFilesystem(
            get_object(pool_object_path),
            {"origin": origin_fs_object_path, "snapshot_name": namespace.snapshot_name},
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if not changed:
            raise StratisCliNoChangeError("snapshot", namespace.snapshot_name)

    @staticmethod
    def rename_fs(namespace):
        """
        Rename a filesystem.

        :raises StratisCliEngineError:
        :raises StratisCliNoChangeError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import Filesystem, ObjectManager, filesystems, pools

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

        ((changed, _), return_code, message) = Filesystem.Methods.SetName(
            get_object(fs_object_path), {"name": namespace.new_name}
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if not changed:
            raise StratisCliNoChangeError("rename", namespace.new_name)

    @staticmethod
    def set_size_limit(namespace):  # pylint: disable=too-many-locals
        """
        Set an upper limit on the size of the filesystem.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import Filesystem, MOFilesystem, ObjectManager, filesystems, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )
        (fs_object_path, fs_info) = next(
            filesystems(props={"Name": namespace.fs_name, "Pool": pool_object_path})
            .require_unique_match(True)
            .search(managed_objects)
        )

        limit = namespace.limit
        mofs = MOFilesystem(fs_info)

        new_limit = str(mofs.Size() if limit == "current" else limit[0].magnitude)

        valid, maybe_size_limit = mofs.SizeLimit()

        if valid and new_limit == maybe_size_limit:
            raise StratisCliFsSizeLimitChangeError(
                Range(new_limit) if limit == "current" else limit[1]
            )

        Filesystem.Properties.SizeLimit.Set(
            get_object(fs_object_path), (True, new_limit)
        )

    @staticmethod
    def unset_size_limit(namespace):
        """
        Unset upper limit on the size of the filesystem.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import Filesystem, MOFilesystem, ObjectManager, filesystems, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": namespace.pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )
        (fs_object_path, fs_info) = next(
            filesystems(props={"Name": namespace.fs_name, "Pool": pool_object_path})
            .require_unique_match(True)
            .search(managed_objects)
        )

        valid, _ = MOFilesystem(fs_info).SizeLimit()

        if not valid:
            raise StratisCliFsSizeLimitChangeError(None)

        Filesystem.Properties.SizeLimit.Set(get_object(fs_object_path), (False, ""))
