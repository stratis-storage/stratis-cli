"""
Miscellaneous physical actions.
"""

from __future__ import print_function

from .._errors import StratisCliUnimplementedError

from .._connection import get_object

from .._constants import TOP_OBJECT

from .._dbus import Manager
from .._dbus import Pool

from .._errors import StratisCliRuntimeError

from .._stratisd_constants import StratisdErrorsGen


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
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.name)

        stratisd_errors = StratisdErrorsGen.get_object()
        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        pool_object = get_object(pool_object_path)
        (result, rc, message) = Pool(pool_object).ListDevs()
        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        for item in result:
            print(item)

        return

    @staticmethod
    def add_device(namespace):
        """
        Add a device to a pool.
        """
        # pylint: disable=unused-argument
        raise StratisCliUnimplementedError('No way to add a device to a pool.')
