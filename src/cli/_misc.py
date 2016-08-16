"""
Miscellaneous helpful methods.
"""

from ._constants import BUS
from ._constants import SERVICE

def get_object(object_path):
    """
    Get an object from an object path.

    :param str object_path: an object path with a valid format
    :returns: the proxy object corresponding to the object path
    :rtype: ProxyObject
    """
    return BUS.get_object(SERVICE, object_path)
