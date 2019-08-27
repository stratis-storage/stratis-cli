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

from ._stratisd_constants import STRATISD_ERROR_TO_NAME


class StratisCliError(Exception):
    """
    Top-level stratis cli error.
    """


class StratisCliRuntimeError(StratisCliError):
    """
    Exception raised during runtime.
    """


class StratisCliUnknownInterfaceError(StratisCliRuntimeError):
    """
    Error raised when code encounters an unexpected D-Bus interface name.
    """

    def __init__(self, interface_name):
        """ Initializer.

            :param str interface_name: the unexpected interface name
        """
        # pylint: disable=super-init-not-called
        self._interface_name = interface_name

    # pylint: disable=fixme
    # FIXME: remove no coverage pragma when adequate testing for CLI output
    # exists.
    def __str__(self):  # pragma: no cover
        return "unexpected interface name %s" % self._interface_name


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

    # pylint: disable=fixme
    # FIXME: remove no coverage pragma when adequate testing for CLI output
    # exists.
    def __str__(self):  # pragma: no cover
        return "%s: %s" % (STRATISD_ERROR_TO_NAME(self.rc), self.message)


class StratisCliActionError(StratisCliRuntimeError):
    """
    Raised if an action selected by the parser failed.
    """

    def __init__(self, command_line_args, namespace):
        """
        Initialize with parser-returned namespace.

        :param command_line_args: the arguments passed on the command line
        :type command_line_args: list of str
        :param Namespace namespace: the namespace constructed by the parser
        """
        # pylint: disable=super-init-not-called
        self.command_line_args = command_line_args
        self.namespace = namespace

    # pylint: disable=fixme
    # FIXME: remove no coverage pragma when adequate testing for CLI output
    # exists.
    def __str__(self):  # pragma: no cover
        fmt_str = (
            "Action selected by command-line arguments %s which were "
            "parsed to %s failed"
        )
        return fmt_str % (self.command_line_args, self.namespace)


class StratisCliGenerationError(StratisCliError):
    """
    Exception that occurs during generation of classes.
    """
