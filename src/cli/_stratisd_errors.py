"""
Representing stratisd errors.
"""

import sys

import dbus

from ._constants import BUS
from ._constants import SERVICE
from ._constants import SERVICE_UNKNOWN_ERROR
from ._constants import TOP_OBJECT

from ._dbus import Manager


class StratisdErrorsGen(object):
    """
    Simple class to provide access to published stratisd errors.
    """

    _STRATISD_ERRORS = None

    @staticmethod
    def parse_error_list(error_list):
        """
        Parse the list of stratisd errors.

        :param error_list: list of errors published by stratisd
        :type error_list: Array of String * `a * String

        :returns: the values and the descriptions attached to the errors
        :rtype: (dict of String * `a) * (dict of `a * String)
        """

        values = dict()
        descriptions = dict()
        for (key, value, desc) in error_list:
            values[key] = value
            descriptions[value] = desc
        return (values, descriptions)

    @staticmethod
    def build_class(values):
        """
        Build a StratisdErrors class with a bunch of class attributes which
        represent the stratisd errors.

        :param values: the values for the attributes
        :type values: dict of String * Int32
        :rtype: type
        :returns: StratisdError class
        """
        return type('StratisdErrors', (object,), values)

    @staticmethod
    def get_class(error_list):
        """
        Get a class from ``error_list``.

        :param error_list: list of errors published by stratisd
        :type error_list: Array of String * `a * String

        :returns: the class which supports a mapping from error codes to ints
        :rtype: type
        """
        (values, _) = StratisdErrorsGen.parse_error_list(error_list)
        return StratisdErrorsGen.build_class(values)

    @staticmethod
    def get_errors():
        """
        Read the available stratisd errors from the bus.

        :return: StratisdErrors class with class attributes for stratisd errors
        :rtype: type
        """
        if StratisdErrorsGen._STRATISD_ERRORS is None:
            try:
                error_codes = \
                   Manager(BUS.get_object(SERVICE, TOP_OBJECT)).GetErrorCodes()
                StratisdErrorsGen._STRATISD_ERRORS = \
                   StratisdErrorsGen.get_class(error_codes)
            except dbus.exceptions.DBusException as err:
                message = str(err)
                if message.startswith(SERVICE_UNKNOWN_ERROR):
                    sys.exit('Service %s unavailable.' % SERVICE)
                raise err

        return StratisdErrorsGen._STRATISD_ERRORS
