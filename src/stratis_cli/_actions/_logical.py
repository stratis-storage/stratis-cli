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

from stratisd_client_dbus import Filesystem
from stratisd_client_dbus import Pool
from stratisd_client_dbus import StratisdErrorsGen
from stratisd_client_dbus import get_managed_objects
from stratisd_client_dbus import get_object
from stratisd_client_dbus import GMOFilesystem

from .._errors import StratisCliRuntimeError

from .._constants import TOP_OBJECT

from ._misc import GetObjectPath


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
        pool_object = get_object(
           GetObjectPath.get_pool(proxy, spec={'Name': namespace.pool_name})
        )

        (_, rc, message) = \
           Pool.CreateFilesystems(pool_object, specs=namespace.fs_name)

        if rc != StratisdErrorsGen().get_object().OK:
            raise StratisCliRuntimeError(rc, message)

        return

    @staticmethod
    def list_volumes(namespace):
        """
        List the volumes in a pool.
        """
        proxy = get_object(TOP_OBJECT)

        pool_object_path = \
           GetObjectPath.get_pool(proxy, spec={'Name': namespace.pool_name})

        for _, info in get_managed_objects(proxy).filesystems(
                   props={'Pool': pool_object_path}
           ):
            print(GMOFilesystem(info).Name())

        return

    @staticmethod
    def destroy_volumes(namespace):
        """
        Destroy volumes in a pool.

        :raises StratisCliRuntimeError:
        """
        proxy = get_object(TOP_OBJECT)
        pool_object_path = \
           GetObjectPath.get_pool(proxy, spec={'Name': namespace.pool_name})

        fs_object_paths = [
           op for name in namespace.fs_name for (op, _) in \
           get_managed_objects(proxy).filesystems(
              props={'Name': name, 'Pool': pool_object_path}
           )
        ]

        (_, rc, message) = \
           Pool.DestroyFilesystems(
              get_object(pool_object_path),
              filesystems=fs_object_paths
           )

        if rc != StratisdErrorsGen().get_object().OK:
            raise StratisCliRuntimeError(rc, message)

        return

    @staticmethod
    def snapshot(namespace):
        """
        Create a snapshot of an existing volume.
        """
        proxy = get_object(TOP_OBJECT)
        pool_object_path = \
           GetObjectPath.get_pool(proxy, spec={'Name': namespace.pool})

        volume_object = get_object(
           GetObjectPath.get_filesystem(
              proxy,
              spec={'Name': namespace.origin, 'Pool': pool_object_path}
           )
        )

        (_, rc, message) = \
           Filesystem.CreateSnapshot(volume_object, names=namespace.volume)
        if rc != StratisdErrorsGen().get_object().OK:
            raise StratisCliRuntimeError(rc, message)

        return
