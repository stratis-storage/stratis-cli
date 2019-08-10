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

from ._data import pools


def get_objects(
    # pylint: disable=bad-continuation
    pool_name,
    managed_objects,
    search_function,
    constructor,
):
    """
    Get objects restricted by optional pool_name. If pool name is None get
    objects for all pools. Returns objects of interest.

    :param pool_name: specifying pool
    :type pool_name: str or None
    :param dict managed_objects: the result of a GetManagedObjects call
    :param search_function: function that finds objects of a given type
    :type search_function: dict -> (dict -> list of str * dict)
    :param constructor: function to wrap dict info about a given object

    :returns: objects of interest
    :rtype: list
    """
    return [
        constructor(info)
        for _, info in search_function(
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
