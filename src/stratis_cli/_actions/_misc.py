"""
Miscellaneous shared methods.
"""

from .._connection import get_object

from .._dbus import Manager

from .._errors import StratisCliRuntimeError

from .._stratisd_constants import StratisdErrorsGen

def get_pool(top, name):
    """
    Get pool.

    :param top: the top object
    :param str name: the name of the pool
    :returns: an object corresponding to ``name``
    :rtype: ProxyObject
    :raises StratisCliRuntimeError: if failure to get object
    """
    (pool_object_path, rc, message) = \
        Manager(top).GetPoolObjectPath(name)

    if rc != StratisdErrorsGen.get_object().STRATIS_OK:
        raise StratisCliRuntimeError(rc, message)

    return get_object(pool_object_path)
