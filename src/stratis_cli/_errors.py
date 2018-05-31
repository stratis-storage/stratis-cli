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
    pass


class StratisCliRuntimeError(StratisCliError):
    """
    Exception raised during runtime.
    """
    pass


class StratisCliUniqueLookupError(StratisCliRuntimeError):
    """
    Error raised when an unique object path is not found for a given
    specification.
    """

    def __init__(self, matches):
        """
        Initializer.

        :param matches: the list of matches actually found
        :type matches: list of object path * dict
        """
        # pylint: disable=super-init-not-called
        self.matches = matches

    def __str__(self):
        return "No unique item found among returned matches: (%s)" % \
            ", ".join(str(x) for x in self.matches)


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

    def __str__(self):
        fmt_str = ("Action selected by command-line arguments %s which were "
                   "parsed to %s failed")
        return fmt_str % (self.command_line_args, self.namespace)


class StratisCliGenerationError(StratisCliError):
    """
    Exception that occurs during generation of classes.
    """
    pass
