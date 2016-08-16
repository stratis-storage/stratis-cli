"""
Miscellaneous top-level actions.
"""

from __future__ import print_function

from .._constants import BUS
from .._constants import SERVICE
from .._constants import TOP_OBJECT

from .._dbus import Manager

from .._errors import StratisCliRuntimeError
from .._errors import StratisCliUnimplementedError
from .._errors import StratisCliValueUnimplementedError

from .._stratisd_errors import StratisdErrorsGen

class TopActions(object):
    """
    Top level actions.
    """

    @staticmethod
    def create_pool(namespace):
        """
        Create a stratis pool.
        """
        if namespace.force:
            raise StratisCliValueUnimplementedError(
               namespace.force,
               "namespace.force"
            )

        if namespace.redundancy != 'none':
            raise StratisCliValueUnimplementedError(
               namespace.redundancy,
               "namespace.redundancy"
            )

        proxy = BUS.get_object(SERVICE, TOP_OBJECT)

        (result, rc, message) = Manager(proxy).CreatePool(
           namespace.name,
           namespace.device,
           0
        )

        if rc == 0:
            print("New pool with object path: %s" % result)

        return (rc, message)

    @staticmethod
    def list_pools(namespace):
        """
        List all stratis pools.
        """
        # pylint: disable=unused-argument
        proxy = BUS.get_object(SERVICE, TOP_OBJECT)

        (result, rc, message) = Manager(proxy).ListPools()
        if rc != 0:
            return (rc, message)

        for item in result:
            print(item)
        return (rc, message)

    @staticmethod
    def destroy_pool(namespace):
        """
        Destroy a stratis pool.

        If no pool exists, the method succeeds.

        :raises StratisCliRuntimeError:
        """
        stratisd_errors = StratisdErrorsGen.get_errors()

        proxy = BUS.get_object(SERVICE, TOP_OBJECT)
        (pool_object_path, rc, message) = \
            Manager(proxy).GetPoolObjectPath(namespace.name)

        if rc == stratisd_errors.STRATIS_POOL_NOTFOUND:
            return

        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        # FIXME: Now, check if pool is burdened with data
        raise StratisCliUnimplementedError(
           "Do not know how to check if pool has data."
        )

        # FIXME: if force and no data can go ahead, otherwise, clean up.
        # pylint: disable=unreachable
        if namespace.force:
            raise StratisCliValueUnimplementedError(
               namespace.force,
               "namespace.force"
            )

        (result, rc, message) = Manager(proxy).DestroyPool(namespace.name)

        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)
        return

    @staticmethod
    def rename_pool(namespace):
        """
        Rename a pool.
        """
        # pylint: disable=unused-argument
        raise StratisCliUnimplementedError("No rename facility available.")
