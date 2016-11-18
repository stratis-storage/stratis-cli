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
from stratisd_client_dbus import get_object

from .._errors import StratisCliRuntimeError


_MN = Manager.MethodNames

def get_pool(top, name):
    """
    Get pool.

    :param top: the top object
    :param str name: the name of the pool
    :returns: an object corresponding to ``name``
    :rtype: ProxyObject
    :raises StratisCliRuntimeError: if failure to get object
    """
    (pool_object_path, rc, message) = \
        Manager.callMethod(top, _MN.GetPoolObjectPath, name)

    if rc != StratisdErrorsGen.get_object().OK:
        raise StratisCliRuntimeError(rc, message)

    return get_object(pool_object_path)

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
    (volume_object_path, rc, message) = \
       Manager.callMethod(top, _MN.GetFilesystemObjectPath, pool, name)

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
       Manager.callMethod(top, _MN.GetCacheObjectPath, pool)

    if rc != StratisdErrorsGen.get_object().OK:
        raise StratisCliRuntimeError(rc, message)

    return get_object(cache_object_path)
