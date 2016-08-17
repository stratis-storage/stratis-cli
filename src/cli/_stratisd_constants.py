"""
Representing stratisd contants.
"""

import abc
import sys

import dbus

from six import add_metaclass

from ._connection import get_object

from ._constants import SERVICE
from ._constants import SERVICE_UNKNOWN_ERROR
from ._constants import TOP_OBJECT

from ._dbus import Manager


class StratisdConstants(object):
    """
    Simple class to provide access to published stratisd constants.
    """

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
    def build_class(classname, values):
        """
        Build a StratisdErrors class with a bunch of class attributes which
        represent the stratisd errors.

        :param str classname: the name of the class to construct
        :param values: the values for the attributes
        :type values: dict of String * Int32
        :rtype: type
        :returns: StratisdError class
        """
        return type(classname, (object,), values)

    @staticmethod
    def get_class(classname, error_list):
        """
        Get a class from ``error_list``.

        :param str classname: the name of the class to construct
        :param error_list: list of errors published by stratisd
        :type error_list: Array of String * `a * String

        :returns: the class which supports a mapping from error codes to ints
        :rtype: type
        """
        (values, _) = StratisdConstants.parse_error_list(error_list)
        return StratisdConstants.build_class(classname, values)


@add_metaclass(abc.ABCMeta)
class StratisdConstantsGen(object):
    """
    Meta class for generating classes that define constants as class-level
    attributes.
    """
    # pylint: disable=too-few-public-methods

    _VALUES = None
    _CLASSNAME = abc.abstractproperty(doc="the name of the class to construct")
    _METHODNAME = abc.abstractproperty(doc="dbus method name")

    @classmethod
    def get_object(cls):
        """
        Read the available list from the bus.

        :return: class with class attributes for stratisd constants
        :rtype: type
        """
        if cls._VALUES is None:
            try:
                values = \
                   getattr(Manager(get_object(TOP_OBJECT)), cls._METHODNAME)()
                cls._VALUES = StratisdConstants.get_class(
                   cls._CLASSNAME,
                   values
                )
            except dbus.exceptions.DBusException as err:
                message = str(err)
                if message.startswith(SERVICE_UNKNOWN_ERROR):
                    sys.exit('Service %s unavailable.' % SERVICE)
                raise err

        return cls._VALUES


class StratisdErrorsGen(StratisdConstantsGen):
    """
    Simple class to provide access to published stratisd errors.
    """
    # pylint: disable=too-few-public-methods

    _CLASSNAME = 'StratisdErrors'
    _METHODNAME = 'GetErrorCodes'
