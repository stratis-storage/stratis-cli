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

from .._connection import get_object

from .._constants import REDUNDANCY
from .._constants import TOP_OBJECT

from .._dbus import Manager

from .._errors import StratisCliRuntimeError
from .._errors import StratisCliUnimplementedError
from .._errors import StratisCliValueError

from .._stratisd_constants import StratisdErrorsGen
from .._stratisd_constants import StratisdRaidGen

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

        try:
            redundancy = REDUNDANCY.get(namespace.redundancy)
        except KeyError:
            raise StratisCliValueError(
               namespace.redundancy,
               "namespace.redundancy",
               "has no corresponding value"
            )

        stratisd_redundancies = StratisdRaidGen.get_object()
        try:
            redundancy_number = getattr(stratisd_redundancies, redundancy)
        except AttributeError:
            raise StratisCliValueError(
               namespace.redundancy,
               "namespace.redundancy",
               "has no corresponding value"
            )

        (_, rc, message) = Manager(proxy).CreatePool(
           namespace.name,
           namespace.device,
           redundancy_number,
           namespace.force
        )

        if rc != stratisd_errors.STRATIS_OK:
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

        (result, rc, message) = Manager(proxy).ListPools()

        stratisd_errors = StratisdErrorsGen.get_object()
        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        for item in result:
            print(item)

        return

    @staticmethod
    def destroy_pool(namespace):
        """
        Destroy a stratis pool.

        If no pool exists, the method succeeds.

        :raises StratisCliRuntimeError:
        """
        proxy = get_object(TOP_OBJECT)

        (_, rc, message) = \
           Manager(proxy).DestroyPool(namespace.name, namespace.force)

        stratisd_errors = StratisdErrorsGen.get_object()

        if rc == stratisd_errors.STRATIS_POOL_NOTFOUND:
            return

        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        return

    @staticmethod
    def rename_pool(namespace):
        """
        Rename a pool.
        """
        # pylint: disable=unused-argument
        raise StratisCliUnimplementedError("No rename facility available.")
