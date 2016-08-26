"""
Actions on a pool's cache.
"""

from __future__ import print_function

from .._errors import StratisCliUnimplementedError
from .._errors import StratisCliValueUnimplementedError

from .._connection import get_object

from .._constants import TOP_OBJECT

from .._dbus import Manager
from .._dbus import Pool


class CacheActions(object):
    """
    Actions on a pool's cache.
    """

    @staticmethod
    def add_devices(namespace):
        """
        Add devices to a cache.
        """
        # pylint: disable=unused-argument
        raise StratisCliUnimplementedError(
           'Not sure how to add a device to an already existing cache.'
        )


    @staticmethod
    def create_cache(namespace):
        """
        Create cache for an existing pool.
        """
        if namespace.redundancy != 'none':
            raise StratisCliValueUnimplementedError(
               namespace.redundancy,
               "namespace.redundancy",
               "unable to handle redundancy"
            )

        proxy = get_object(TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.pool)
        if rc != 0:
            return (rc, message)

        pool_object = get_object(pool_object_path)
        (result, rc, message) = Pool(pool_object).AddCache(namespace.device)
        if rc != 0:
            return (rc, message)

        print("Object path for pool: %s" % result)
        return (rc, message)

    @staticmethod
    def list_cache(namespace):
        """
        List information about the cache belonging to a pool.
        """
        proxy = get_object(TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.pool)
        if rc != 0:
            return (rc, message)

        pool_object = get_object(pool_object_path)
        (result, rc, message) = Pool(pool_object).ListCache()
        if rc != 0:
            return (rc, message)

        for item in result:
            print(item)

        return (rc, message)

    @staticmethod
    def remove_device(namespace):
        """
        Remove a device from the given pool.
        """
        proxy = get_object(TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.pool)
        if rc != 0:
            return (rc, message)

        pool_object = get_object(pool_object_path)
        return Pool(pool_object).RemoveCache()
