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
from stratisd_client_dbus import StratisdErrorsGen
from stratisd_client_dbus import get_object

from .._constants import TOP_OBJECT

from .._errors import StratisCliRuntimeError
from .._errors import StratisCliValueError

from ._misc import get_pool_object_by_name
from ._misc import pools


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
        stratisd_errors = StratisdErrorsGen.get_object()

        proxy = get_object(TOP_OBJECT)


        (_, rc, message) = Manager.CreatePool(
           proxy,
           name=namespace.name,
           redundancy=0,
           force=namespace.force,
           devices=namespace.device
        )

        if rc != stratisd_errors.OK:
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
        for _, info in pools(proxy):
            print(info.name())

        return

    @staticmethod
    def destroy_pool(namespace):
        """
        Destroy a stratis pool.

        If no pool exists, the method succeeds.

        :raises StratisCliRuntimeError:
        """
        proxy = get_object(TOP_OBJECT)

        (_, rc, message) = Manager.DestroyPool(proxy, name=namespace.name)

        stratisd_errors = StratisdErrorsGen.get_object()

        if rc != stratisd_errors.OK:
            raise StratisCliRuntimeError(rc, message)

        return

    @staticmethod
    def rename_pool(namespace):
        """
        Rename a pool.
        """
        proxy = get_object(TOP_OBJECT)
        (pool, _) = get_pool_object_by_name(proxy, namespace.current)
        if pool is None:
            raise StratisCliValueError(
               namespace.current,
               "current",
               "no pool with the given name"
            )
        (_, rc, message) = Pool.SetName(pool, new_name=namespace.new)

        stratisd_errors = StratisdErrorsGen.get_object()
        if rc != stratisd_errors.OK:
            raise StratisCliRuntimeError(rc, message)

        return
