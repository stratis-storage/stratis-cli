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


class StratisCliRuntimeError(StratisCliError):
    """
    Exception raised during runtime.
    """
    pass


class StratisCliDbusLookupError(StratisCliRuntimeError):
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
        self.interface = interface
        self.spec = spec

    def __str__(self):  # pragma: no cover
        return "No object path found for interface %s and spec %s" % \
           (self.interface, self.spec)


class StratisCliEngineError(StratisCliRuntimeError):
    """
    Raised if there was a failure due to an error in stratisd's engine.
    """

    def __init__(self, rc, message):
        """ Initializer.

            :param rc int: the error code returned by the engine
            :param str message: whatever message accompanied the error code
        """
        # pylint: disable=super-init-not-called
        self.rc = rc
        self.message = message

    def __str__(self):
        return "%s: %s" % (self.rc, self.message)


class StratisCliGenerationError(StratisCliError):
    """
    Exception that occurs during generation of classes.
    """
    pass
