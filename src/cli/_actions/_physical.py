"""
Miscellaneous physical actions.
"""

from __future__ import print_function

from .._errors import StratisCliValueUnimplementedError

from .._constants import BUS
from .._constants import SERVICE
from .._constants import TOP_OBJECT

from .._dbus import Manager
from .._dbus import Pool


class PhysicalActions(object):
    """
    Actions on the physical aspects of a pool.
    """

    @staticmethod
    def list_pool(namespace):
        """
        List devices in a pool.
        """
        proxy = BUS.get_object(SERVICE, TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.name)
        if rc != 0:
            return (rc, message)

        pool_object = BUS.get_object(SERVICE, pool_object_path)
        (result, rc, message) = Pool(pool_object).ListDevs()
        if rc != 0:
            return (rc, message)

        for item in result:
            print(item)

        return (rc, message)
