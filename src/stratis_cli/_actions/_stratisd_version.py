"""
Check version of stratisd
"""

from .._errors import StratisCliStratisdVersionError
from ._connection import get_object
from ._constants import TOP_OBJECT


def check_stratisd_version():
    """
    Checks that the version of stratisd that is running is compatible with
    this version of the CLI

    :raises StratisCliStratisdVersionError
    """
    from ._constants import MAXIMUM_STRATISD_VERSION, MINIMUM_STRATISD_VERSION
    from ._data import Manager

    version = Manager.Properties.Version.Get(get_object(TOP_OBJECT))
    version = tuple([int(x) for x in version.split(".")])
    if version < MINIMUM_STRATISD_VERSION or version > MAXIMUM_STRATISD_VERSION:
        raise StratisCliStratisdVersionError(
            version, MINIMUM_STRATISD_VERSION, MAXIMUM_STRATISD_VERSION
        )
