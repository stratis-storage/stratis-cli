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
Miscellaneous physical actions.
"""

from __future__ import print_function

from .._connection import get_object

from .._constants import TOP_OBJECT

from .._dbus import Pool

from .._errors import StratisCliRuntimeError

from .._stratisd_constants import StratisdErrorsGen

from ._misc import get_pool


class PhysicalActions(object):
    """
    Actions on the physical aspects of a pool.
    """

    @staticmethod
    def list_pool(namespace):
        """
        List devices in a pool.
        """
        proxy = get_object(TOP_OBJECT)
        pool_object = get_pool(proxy, namespace.name)
        (result, rc, message) = Pool(pool_object).ListDevs()
        if rc != StratisdErrorsGen.get_object().STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        for item in result:
            print(item)

        return

    @staticmethod
    def add_device(namespace):
        """
        Add a device to a pool.
        """
        proxy = get_object(TOP_OBJECT)
        pool_object = get_pool(proxy, namespace.name)
        (_, rc, message) = Pool(pool_object).AddDevs(namespace.device)
        if rc != StratisdErrorsGen.get_object().STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)
        return
