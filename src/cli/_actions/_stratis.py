"""
Miscellaneous actions about stratis.
"""

from __future__ import print_function

from .._constants import BUS
from .._constants import SERVICE
from .._constants import TOP_OBJECT

from .._dbus import Manager


class StratisActions(object):
    """
    Stratis actions.
    """
    # pylint: disable=too-few-public-methods

    @staticmethod
    def list_stratisd_log_level(namespace):
        """
        List the stratisd log level.
        """
        # pylint: disable=unused-argument
        proxy = BUS.get_object(SERVICE, TOP_OBJECT)
        print(Manager(proxy).LogLevel)
        return (0, 'ok')

    @staticmethod
    def list_stratisd_version(namespace):
        """
        List the stratisd version.
        """
        # pylint: disable=unused-argument
        proxy = BUS.get_object(SERVICE, TOP_OBJECT)
        print(Manager(proxy).Version)
        return (0, 'ok')

    @staticmethod
    def dispatch(namespace):
        """
        Dispatch to the correct function.
        """
        if namespace.stratisd_log_level:
            return StratisActions.list_stratisd_log_level(namespace)

        if namespace.stratisd_version:
            return StratisActions.list_stratisd_version(namespace)

        assert False
