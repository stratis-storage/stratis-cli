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

from .._stratisd_constants import StratisdErrors

from ._connection import get_object
from ._data import MOFilesystem
from ._data import ObjectManager
from ._data import Pool
from ._data import Filesystem
from ._data import filesystems
from ._data import pools
from ._formatting import print_table
from ._util import get_objects
from ._util import verify_stratisd_version_decorator


class LogicalActions():
    """
    Actions on the logical aspects of a pool.
    """

    @staticmethod
    @verify_stratisd_version_decorator
    def create_volumes(namespace, proxy):
        """
        Create volumes in a pool.

        :raises StratisCliEngineError:
        """
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={
                'Name': namespace.pool_name
            }).require_unique_match(True).search(managed_objects))

        (_, rc, message) = Pool.Methods.CreateFilesystems(
            get_object(pool_object_path), {'specs': namespace.fs_name})

        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)

    @staticmethod
    @verify_stratisd_version_decorator
    def list_volumes(namespace, proxy):
        """
        List the volumes in a pool.
        """
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (mofilesystems, path_to_name) = get_objects(
            namespace, "pool_name", managed_objects, filesystems, MOFilesystem)

        tables = [[
            path_to_name[mofilesystem.Pool()],
            mofilesystem.Name(),
            str(Range(mofilesystem.Used())),
            date_parser.parse(mofilesystem.Created()).astimezone().strftime(
                "%b %d %Y %H:%M"),
            mofilesystem.Devnode(),
            mofilesystem.Uuid(),
        ] for mofilesystem in mofilesystems]

        print_table(['Pool Name', 'Name', 'Used', 'Created', 'Device', 'UUID'],
                    sorted(tables, key=lambda entry: entry[0]),
                    ['<', '<', '<', '<', '<', '<'])

    @staticmethod
    @verify_stratisd_version_decorator
    def destroy_volumes(namespace, proxy):
        """
        Destroy volumes in a pool.

        :raises StratisCliEngineError:
        """
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, _) = next(
            pools(props={
                'Name': namespace.pool_name
            }).require_unique_match(True).search(managed_objects))
        fs_object_paths = [
            op for name in namespace.fs_name
            for (op, _) in filesystems(props={
                'Name': name,
                'Pool': pool_object_path
            }).search(managed_objects)
        ]

        (_, rc, message) = Pool.Methods.DestroyFilesystems(
            get_object(pool_object_path), {'filesystems': fs_object_paths})

        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)

    @staticmethod
    @verify_stratisd_version_decorator
    def snapshot_filesystem(namespace, proxy):
        """
        Snapshot filesystem in a pool.

        :raises StratisCliEngineError:
        """
        import time
        before = time.time()
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        after = time.time()
        print("Elapsed time for GetManagedObjects call = %f" %
              (after - before))

        (pool_object_path, _) = next(
            pools(props={
                'Name': namespace.pool_name
            }).require_unique_match(True).search(managed_objects))
        (origin_fs_object_path, _) = next(
            filesystems(props={
                'Name': namespace.origin_name,
                'Pool': pool_object_path
            }).require_unique_match(True).search(managed_objects))

        before = time.time()
        (_, rc, message) = Pool.Methods.SnapshotFilesystem(
            get_object(pool_object_path), {
                'origin': origin_fs_object_path,
                'snapshot_name': namespace.snapshot_name
            })
        after = time.time()
        print("Elapsed time for SnapshotFilesystem call = %f" %
              (after - before))

        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)

    @staticmethod
    @verify_stratisd_version_decorator
    def rename_fs(namespace, proxy):
        """
        Rename a filesystem.
        """
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={
                'Name': namespace.pool_name
            }).require_unique_match(True).search(managed_objects))
        (fs_object_path, _) = next(
            filesystems(props={
                'Name': namespace.fs_name,
                'Pool': pool_object_path
            }).require_unique_match(True).search(managed_objects))

        (_, rc, message) = Filesystem.Methods.SetName(
            get_object(fs_object_path), {'name': namespace.new_name})

        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)
