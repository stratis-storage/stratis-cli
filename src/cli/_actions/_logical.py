"""
Miscellaneous logical actions.
"""

from __future__ import print_function

from .._errors import StratisCliRuntimeError
from .._errors import StratisCliUnimplementedError

from .._constants import TOP_OBJECT

from .._dbus import Manager
from .._dbus import Pool

from .._misc import get_object

from .._stratisd_errors import StratisdErrorsGen


class LogicalActions(object):
    """
    Actions on the logical aspects of a pool.
    """

    @staticmethod
    def create_volumes(namespace):
        """
        Create volumes in a pool.

        :raises StratisCliRuntimeError:
        """
        stratisd_errors = StratisdErrorsGen.get_errors()

        proxy = get_object(TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.pool)

        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        pool_object = get_object(pool_object_path)
        (_, rc, message) = \
            Pool(pool_object).CreateVolumes(namespace.volume)

        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        return

    @staticmethod
    def list_volumes(namespace):
        """
        List the volumes in a pool.
        """
        proxy = get_object(TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.pool)
        if rc != 0:
            return (rc, message)

        pool_object = get_object(pool_object_path)
        (result, rc, message) = Pool(pool_object).ListVolumes()

        for item in result:
            print(item)

        return (rc, message)

    @staticmethod
    def destroy_volumes(namespace):
        """
        Destroy volumes in a pool.
        """
        proxy = get_object(TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.pool)
        if rc != 0:
            return (rc, message)

        _ = get_object(pool_object_path)
        raise StratisCliUnimplementedError(
           'Waiting until DestroyVolume becomes DestroyVolumes'
        )

    @staticmethod
    def snapshot(namespace):
        """
        Create a snapshot of an existing volume.
        """
        proxy = get_object(TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.pool)
        if rc != 0:
            return (rc, message)

        _ = get_object(pool_object_path)
        raise StratisCliUnimplementedError(
           "Do not know how to do a snapshot at this time."
        )
