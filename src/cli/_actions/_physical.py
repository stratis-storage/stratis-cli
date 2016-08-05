"""
Miscellaneous physical actions.
"""

from __future__ import print_function

from .._errors import StratisCliValueUnimplementedError

from ._lib import object_from_name

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
        dbus_object = object_from_name(namespace.name)
        (result, rc, message) = Pool(dbus_object).ListDevs()
        if rc != 0:
            return (rc, message)

        for item in result:
            print(item)

        return (rc, message)
