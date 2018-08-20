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
Shared utilities.
"""

from __future__ import print_function

from ._data import MOPool
from ._data import pools
from ._data import unique


def get_pools(namespace, pool_name_key, managed_objects):
    """
    Get pools specified by namespace and designated pool_name_key.
    If no pool is specified in namespace, get all pools.

    :param namespace: the parser namespace
    :param str pool_name_key: the key in the namespace for the pool name
    :param managed_objects: the result of a GetManagedObjects call

    :returns: lookup properties and a map from pool object path to name
    :rtype: dict * dict
    """
    if getattr(namespace, pool_name_key, None) is not None:
        (parent_pool_object_path, _) = unique(
            pools(props={
                'Name': namespace.pool_name
            }).search(managed_objects))

        properties = {"Pool": parent_pool_object_path}
        path_to_name = {parent_pool_object_path: namespace.pool_name}
    else:
        properties = {}
        path_to_name = dict((path, MOPool(info).Name())
                            for path, info in pools().search(managed_objects))

    return (properties, path_to_name)
