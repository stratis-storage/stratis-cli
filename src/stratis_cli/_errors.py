# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Error heirarchy for stratis cli.
"""


class StratisCliError(Exception):
    """
    Top-level stratis cli error.
    """
    pass


class StratisCliDbusLookupError(StratisCliError):
    """
    Error raised when an object path is not found for a given specification.
    """

    def __init__(self, interface, spec):
        """
        Initializer.

        :param str interface: the specified interface, or some part thereof
        :param spec: the narrowing spec, based on interface properties
        :type spec: a dict of str * object
        """
        # pylint: disable=super-init-not-called
        self._interface = interface
        self._spec = spec

    def __str__(self):  # pragma: no cover
        return "No object path found for interface %s and spec %s" % \
           (self._interface, self._spec)


class StratisCliValueError(StratisCliError):
    """ Raised when a parameter has an unacceptable value.

        May also be raised when the parameter has an unacceptable type.
    """
    _FMT_STR = "value '%s' for parameter %s is unacceptable"

    def __init__(self, value, param, msg=None):
        """ Initializer.

            :param object value: the value
            :param str param: the parameter
            :param str msg: an explanatory message
        """
        # pylint: disable=super-init-not-called
        self._value = value
        self._param = param
        self._msg = msg

    def __str__(self):  # pragma: no cover
        if self._msg:
            fmt_str = self._FMT_STR + ": %s"
            return fmt_str % (self._value, self._param, self._msg)
        return self._FMT_STR % (self._value, self._param)


class StratisCliValueUnimplementedError(StratisCliValueError):
    """
    Raised if a parameter is not intrinsically bad but functionality
    is unimplemented for this value.
    """
    pass


class StratisCliUnimplementedError(StratisCliError):
    """
    Raised if a method is temporarily unimplemented.
    """
    pass


class StratisCliKnownBugError(StratisCliError):
    """
    Raised if a method is unimplemented due to a bug.
    """
    pass


class StratisCliRuntimeError(StratisCliError):
    """
    Raised if there was a failure due to a RuntimeError.
    """

    def __init__(self, rc, message):
        """ Initializer.

            :param object value: the value
            :param str param: the parameter
            :param str msg: an explanatory message
        """
        # pylint: disable=super-init-not-called
        self.rc = rc
        self.message = message

    def __str__(self):
        return "%s: %s" % (self.rc, self.message)


class StratisCliImpossibleError(StratisCliError):
    """
    Raised when a should be logically impossible situation is encountered.
    """
    pass
