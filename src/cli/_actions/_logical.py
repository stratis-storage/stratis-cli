"""
Miscellaneous logical actions.
"""

from __future__ import print_function

from .._errors import StratisCliUnimplementedError

from .._constants import BUS
from .._constants import SERVICE
from .._constants import TOP_OBJECT

from .._dbus import Manager
from .._dbus import Pool


class LogicalActions(object):
    """
    Actions on the logical aspects of a pool.
    """

    @staticmethod
    def create_volumes(namespace):
        """
        Create volumes in a pool.
        """
        proxy = BUS.get_object(SERVICE, TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.pool)
        if rc != 0:
            return (rc, message)

        pool_object = BUS.get_object(SERVICE, pool_object_path)
        raise StratisCliUnimplementedError(
           'Waiting until CreateVolume becomes CreateVolumes'
        )

    @staticmethod
    def list_volumes(namespace):
        """
        List the volumes in a pool.
        """
        proxy = BUS.get_object(SERVICE, TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.pool)
        if rc != 0:
            return (rc, message)

        pool_object = BUS.get_object(SERVICE, pool_object_path)
        (result, rc, message) = Pool(pool_object).ListVolumes()

        for item in result:
            print(item)

        return (rc, message)
