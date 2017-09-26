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
Miscellaneous top-level actions.
"""

from __future__ import print_function

from stratisd_client_dbus import Manager
from stratisd_client_dbus import Pool
from stratisd_client_dbus import get_managed_objects
from stratisd_client_dbus import get_object
from stratisd_client_dbus import GMOPool

from .._constants import TOP_OBJECT

from .._errors import StratisCliRuntimeError

from .._stratisd_constants import StratisdErrors

from ._misc import GetObjectPath


class TopActions(object):
    """
    Top level actions.
    """

    @staticmethod
    def create_pool(namespace):
        """
        Create a stratis pool.

        :raises StratisCliRuntimeError:
        """
        proxy = get_object(TOP_OBJECT)

        (_, rc, message) = Manager.CreatePool(
           proxy,
           name=namespace.pool_name,
           redundancy=0,
           force=namespace.force,
           devices=namespace.blockdevs
        )

        if rc != StratisdErrors.OK:
            raise StratisCliRuntimeError(rc, message)

        return

    @staticmethod
    def list_pools(namespace):
        """
        List all stratis pools.

        :raises StratisCliRuntimeError:
        """
        # pylint: disable=unused-argument
        proxy = get_object(TOP_OBJECT)

        for _, info in get_managed_objects(proxy).pools():
            print(GMOPool(info).Name())

        return

    @staticmethod
    def destroy_pool(namespace):
        """
        Destroy a stratis pool.

        If no pool exists, the method succeeds.

        :raises StratisCliRuntimeError:
        """
        proxy = get_object(TOP_OBJECT)
        pool_object_path = \
           GetObjectPath.get_pool(proxy, spec={'Name': namespace.pool_name})

        (_, rc, message) = \
           Manager.DestroyPool(proxy, pool=pool_object_path)

        if rc != StratisdErrors.OK:
            raise StratisCliRuntimeError(rc, message)

        return

    @staticmethod
    def rename_pool(namespace):
        """
        Rename a pool.
        """
        proxy = get_object(TOP_OBJECT)

        pool_object = get_object(
           GetObjectPath.get_pool(proxy, spec={'Name': namespace.current})
        )

        (_, rc, message) = Pool.SetName(pool_object, name=namespace.new)

        if rc != StratisdErrors.OK:
            raise StratisCliRuntimeError(rc, message)

        return
