"""
Miscellaneous top-level actions.
"""

from __future__ import print_function

from .._connection import get_object

from .._constants import TOP_OBJECT

from .._dbus import Manager

from .._errors import StratisCliRuntimeError
from .._errors import StratisCliUnimplementedError

from .._stratisd_constants import StratisdErrorsGen

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
        stratisd_errors = StratisdErrorsGen.get_object()

        proxy = get_object(TOP_OBJECT)

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

        :raises StratisCliRuntimeError:
        """
        # pylint: disable=unused-argument
        stratisd_errors = StratisdErrorsGen.get_object()

        proxy = get_object(TOP_OBJECT)

        (result, rc, message) = Manager(proxy).ListPools()
        if rc != stratisd_errors.STRATIS_OK:
            raise StratisCliRuntimeError(rc, message)

        for item in result:
            print(item)

        return

    @staticmethod
    def destroy_pool(namespace):
        """
        Destroy a stratis pool.

        If no pool exists, the method succeeds.

        :raises StratisCliRuntimeError:
        """
        stratisd_errors = StratisdErrorsGen.get_object()

        proxy = get_object(TOP_OBJECT)

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
