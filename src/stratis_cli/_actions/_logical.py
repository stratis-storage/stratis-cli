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

from __future__ import print_function

from justbytes import Range
from dateutil import parser as date_parser

from .._errors import StratisCliEngineError

from .._stratisd_constants import StratisdErrors

from ._connection import get_object
from ._constants import TOP_OBJECT
from ._data import MOFilesystem
from ._data import MOPool
from ._data import ObjectManager
from ._data import Pool
from ._data import Filesystem
from ._data import filesystems
from ._data import pools
from ._data import unique
from ._formatting import print_table


class LogicalActions():
    """
    Actions on the logical aspects of a pool.
    """

    @staticmethod
    def create_volumes(namespace):
        """
        Create volumes in a pool.

        :raises StratisCliEngineError:
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = unique(
            pools(props={
                'Name': namespace.pool_name
            }).search(managed_objects))

        (_, rc, message) = Pool.Methods.CreateFilesystems(
            get_object(pool_object_path), {'specs': namespace.fs_name})

        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)

    @staticmethod
    def list_volumes(namespace):
        """
        List the volumes in a pool.
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})


        if getattr(namespace, "pool_name", None) is not None:
            (parent_pool_object_path, _) = unique(
                pools(props={
                    'Name': namespace.pool_name
                }).search(managed_objects))

            properties = {"Pool": parent_pool_object_path}
            path_to_name = {parent_pool_object_path: namespace.pool_name}
        else:
            properties = {}
            path_to_name = dict(
                (path, MOPool(info).Name())
                for path, info in pools().search(managed_objects))


        mofilesystems = [
            MOFilesystem(info)
            for _, info in filesystems(props=properties, ).search(managed_objects)
        ]

        tables = [[
            path_to_name[mofilesystem.Pool()],
            mofilesystem.Name(),
            str(Range(mofilesystem.Used(), 1)),
            date_parser.parse(mofilesystem.Created()).astimezone().strftime("%b %d %Y %H:%M"),
        ] for mofilesystem in mofilesystems]

        print_table(['Pool Name', 'Name', 'Used', 'Created'], sorted(tables, key=lambda entry: entry[0]),
                    ['<', '<', '>', '>'])

    @staticmethod
    def destroy_volumes(namespace):
        """
        Destroy volumes in a pool.

        :raises StratisCliEngineError:
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, _) = unique(
            pools(props={
                'Name': namespace.pool_name
            }).search(managed_objects))
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
    def snapshot_filesystem(namespace):
        """
        Snapshot filesystem in a pool.

        :raises StratisCliEngineError:
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, _) = unique(
            pools(props={
                'Name': namespace.pool_name
            }).search(managed_objects))
        (origin_fs_object_path, _) = unique(
            filesystems(props={
                'Name': namespace.origin_name,
                'Pool': pool_object_path
            }).search(managed_objects))

        (_, rc, message) = Pool.Methods.SnapshotFilesystem(
            get_object(pool_object_path), {
                'origin': origin_fs_object_path,
                'snapshot_name': namespace.snapshot_name
            })

        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)

    @staticmethod
    def rename_fs(namespace):
        """
        Rename a filesystem.
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = unique(
            pools(props={
                'Name': namespace.pool_name
            }).search(managed_objects))
        (fs_object_path, _) = unique(
            filesystems(props={
                'Name': namespace.fs_name,
                'Pool': pool_object_path
            }).search(managed_objects))

        (_, rc, message) = Filesystem.Methods.SetName(
            get_object(fs_object_path), {'name': namespace.new_name})

        if rc != StratisdErrors.OK:
            raise StratisCliEngineError(rc, message)
