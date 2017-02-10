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
Miscellaneous shared methods.
"""

from stratisd_client_dbus import Manager
from stratisd_client_dbus import StratisdErrorsGen
from stratisd_client_dbus import get_managed_objects
from stratisd_client_dbus import get_object

from .._errors import StratisCliRuntimeError

def get_pool_path_by_name(top, name):
    """
    Get pool object path and table info by name.

    :param top: the top object
    :param str name: the name of the pool
    :returns: an object path corresponding to ``name`` or None if there is none
    :rtype: ((ObjectPath * GMOPool) or NoneType) * dict
    """
    objects = get_managed_objects(top)
    result = objects.get_pool_by_name(name)
    if result is None:
        return (None, objects)
    else:
        (pool, table) = result
        return ((pool, GMOPool(table)), objects)

def get_pool_object_by_name(top, name):
    """
    Get pool object by its name.

    :param top: the top object
    :param str name: the name of the pool
    :returns: an object corresponding to ``name`` or None if there is none
    :rtype: (ProxyObject or NoneType) * dict
    """
    (result, objects) = get_pool_path_by_name(top, name)
    if result is None:
        return (None, objects)
    (pool, _) = result
    return (get_object(pool), objects)

def get_volume(top, pool, name):
    """
    Get volume given ``name`` and ``pool``.

    :param top: the top object
    :param str pool: the object path of the pool
    :param str name: the name of the volume

    :returns: the corresponding object
    :rtype: ProxyObject
    :raises StratisCliRuntimeError: if failure to get object
    """
    (volume_object_path, rc, message) = Manager.GetFilesystemObjectPath(
       top,
       pool_name=pool,
       filesystem_name=name
    )

    if rc != StratisdErrorsGen.get_object().OK:
        raise StratisCliRuntimeError(rc, message)

    return get_object(volume_object_path)

def get_cache(top, pool):
    """
    Get cache given ``pool``.

    :param top: the top object
    :param str pool: the name of the pool

    :returns: the corresponding object
    :rtype: ProxyObject
    :raises StratisCliRuntimeError: if failure to get object
    """
    (cache_object_path, rc, message) = \
       Manager.GetCacheObjectPath(top, name=pool)

    if rc != StratisdErrorsGen.get_object().OK:
        raise StratisCliRuntimeError(rc, message)

    return get_object(cache_object_path)
