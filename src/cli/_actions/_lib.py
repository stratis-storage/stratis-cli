"""
Miscellaneous supporting methods.
"""


from .._constants import BUS
from .._constants import TOP_OBJECT
from .._constants import SERVICE


def object_path_from_name(name):
    """
    Get dbus object path from name.

    :param str name: an adequately identifying name
    :return: the object path corresponding to the name
    :rtype: str
    """
    return "%s/%s" % (TOP_OBJECT, name)

def object_from_name(name):
    """
    Get dbus object from name.

    :param bus: the d-bus bus
    :param str name: an adequately identifying name
    :return: the dbus object corresponding to the name
    :rtype: a dbus object
    """
    object_path = object_path_from_name(name)
    return BUS.get_object(SERVICE, object_path)
