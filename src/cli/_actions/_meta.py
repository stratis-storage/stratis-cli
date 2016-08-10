"""
Miscellaneous actions about the program.
"""

from __future__ import print_function

from .._constants import BUS
from .._constants import SERVICE
from .._constants import TOP_OBJECT

from .._dbus import Manager


class MetaActions(object):
    """
    Meta- actions.
    """
    # pylint: disable=too-few-public-methods

    @staticmethod
    def list_stratisd_version(namespace):
        """
        List the stratisd version.
        """
        # pylint: disable=unused-argument
        proxy = BUS.get_object(SERVICE, TOP_OBJECT)
        print(Manager(proxy).Version)
        return (0, 'ok')
