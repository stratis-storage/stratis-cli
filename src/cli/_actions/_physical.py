"""
Miscellaneous physical actions.
"""

from __future__ import print_function

from .._errors import StratisCliUnimplementedError

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
        (result, rc, message) = Pool(pool_object).AddDevs(namespace.device)
        if rc != StratisdErrorsGen.get_object().STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)
        return
