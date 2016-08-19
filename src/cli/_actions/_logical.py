"""
Miscellaneous logical actions.
"""

from __future__ import print_function

from .._errors import StratisCliRuntimeError
from .._errors import StratisCliUnimplementedError

from .._connection import get_object

from .._constants import TOP_OBJECT

from .._dbus import Manager
from .._dbus import Pool

from .._stratisd_constants import StratisdErrorsGen


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
        proxy = get_object(TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.pool)

        stratisd_errors = StratisdErrorsGen.get_object()
        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        volume_list = [(x, '', '') for x in namespace.volume]

        pool_object = get_object(pool_object_path)
        (_, rc, message) = \
            Pool(pool_object).CreateVolumes(volume_list)

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

        stratisd_errors = StratisdErrorsGen.get_object()
        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        pool_object = get_object(pool_object_path)
        (_, rc, message) = \
           Pool(pool_object).DestroyVolumes(namespace.volume, namespace.force)
        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        return

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
