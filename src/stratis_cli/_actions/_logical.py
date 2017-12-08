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

from .._errors import StratisCliRuntimeError

from .._stratisd_constants import StratisdErrors

from ._connection import get_object
from ._constants import TOP_OBJECT
from ._data import MOFilesystem
from ._data import ObjectManager
from ._data import Pool
from ._data import Filesystem
from ._data import filesystems
from ._data import pools


class LogicalActions(object):
    """
    Actions on the logical aspects of a pool.
    """

    @staticmethod
    def create_volumes(namespace):
        """
        Create volumes in a pool.

        :raises StratisCliRuntimeError:
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = pools(
           managed_objects,
           props={'Name': namespace.pool_name},
           unique=True
        )

        (_, rc, message) = Pool.Methods.CreateFilesystems(
           get_object(pool_object_path),
           {'specs': namespace.fs_name}
        )

        if rc != StratisdErrors.OK:
            raise StratisCliRuntimeError(rc, message)

        return

    @staticmethod
    def list_volumes(namespace):
        """
        List the volumes in a pool.
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, _) = pools(
           managed_objects,
           props={'Name': namespace.pool_name},
           unique=True
        )
        matching_filesystems = filesystems(
           managed_objects,
           props={'Pool': pool_object_path}
        )
        for _, info in matching_filesystems:
            print(MOFilesystem(info).Name())

        return

    @staticmethod
    def destroy_volumes(namespace):
        """
        Destroy volumes in a pool.

        :raises StratisCliRuntimeError:
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, _) = pools(
           managed_objects,
           props={'Name': namespace.pool_name},
           unique=True
        )
        fs_object_paths = [
           op for name in namespace.fs_name for (op, _) in \
           filesystems(
              managed_objects,
              props={'Name': name, 'Pool': pool_object_path}
           )
        ]

        (_, rc, message) = \
           Pool.Methods.DestroyFilesystems(
              get_object(pool_object_path),
              {'filesystems': fs_object_paths}
           )

        if rc != StratisdErrors.OK:
            raise StratisCliRuntimeError(rc, message)

        return

    @staticmethod
    def snapshot_filesystem(namespace):
        """
        Snapshot filesystem in a pool.

        :raises StratisCliRuntimeError:
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, _) = pools(
           managed_objects,
           props={'Name': namespace.pool_name},
           unique=True
        )
        (origin_fs_object_path, _) = filesystems(
            managed_objects,
            props={'Name': namespace.origin_name, 'Pool': pool_object_path},
            unique=True
        )

        (_, rc, message) = \
           Pool.Methods.SnapshotFilesystem(
              get_object(pool_object_path),
              {'origin': origin_fs_object_path,
               'snapshot_name': namespace.snapshot_name}
           )

        if rc != StratisdErrors.OK:
            raise StratisCliRuntimeError(rc, message)

        return
    @staticmethod
    def rename_fs(namespace):
        """
        Rename a filesystem.
        """
        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = filesystems(
           managed_objects,
           props={'Name': namespace.fs_name},
           unique=True
        )

        (_, rc, message) = Filesystem.Methods.SetName(
           get_object(pool_object_path),
           {'name': namespace.new_name}
        )

        if rc != StratisdErrors.OK:
            raise StratisCliRuntimeError(rc, message)

        return
