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

from .._stratisd_errors import StratisdErrorsGen

class TopActions(object):
    """
    Top level actions.
    """

    @staticmethod
    def create_pool(namespace):
        """
        Create a stratis pool.

        :raises StratisCliRuntimeError:
        """
        stratisd_errors = StratisdErrorsGen.get_errors()

        proxy = BUS.get_object(SERVICE, TOP_OBJECT)

        raise StratisCliUnimplementedError(
           "Waiting for CreatePool to take force parameter."
        )

        # pylint: disable=unreachable
        (_, rc, message) = Manager(proxy).CreatePool(
           namespace.name,
           namespace.device,
           0,
           namespace.force
        )

        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        return

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

        raise StratisCliUnimplementedError(
           "Waiting for DestroyPool to take force parameter."
        )

        # pylint: disable=unreachable
        (_, rc, message) = \
           Manager(proxy).DestroyPool(namespace.name, namespace.force)

        if rc == stratisd_errors.STRATIS_POOL_NOTFOUND:
            return

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
