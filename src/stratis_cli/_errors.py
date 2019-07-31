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

from ._stratisd_constants import BlockDevTiers
from ._stratisd_constants import BLOCK_DEV_TIER_TO_NAME
from ._stratisd_constants import STRATISD_ERROR_TO_NAME


class StratisCliError(Exception):
    """
    Top-level stratis cli error.
    """


class StratisCliRuntimeError(StratisCliError):
    """
    Exception raised during runtime.
    """


class StratisNoChangeError(StratisCliError):
    """
    Raised if there was a failure due to no changed state in stratisd's engine.
    """

    def __init__(self, command, resource):
        """ Initializer.

            :param str command: the executed command
            :param str resource: the target resource
        """
        # pylint: disable=super-init-not-called
        self.command = command
        self.resource = resource

    def __str__(self):
        return "The command '%s' has already been completed for resource '%s'" % (
            self.command,
            self.resource,
        )


class StratisPartialChangeError(StratisCliError):
    """
    Raised if there was a failure due to partially changed state in stratisd's engine.
    """

    def __init__(self, command, changed_resources, unchanged_resources):
        """ Initializer.

            :param str command: the command run that caused the error
            :param list of str changed_resources: the target resources that would change
            :param list of str unchanged_resources: the target resources that would not change
        """
        # pylint: disable=super-init-not-called
        self.command = command
        self.changed_resources = changed_resources
        self.unchanged_resources = unchanged_resources

    def __str__(self):
        msg = "The command '%s' has already been completed for resources %s " % (
            self.command,
            self.unchanged_resources,
        )
        if self.changed_resources != []:
            msg += "but not yet for resources %s" % self.changed_resources
        return msg


class StratisInUseError(StratisCliError):
    """
    Raised if a block device is added as both a blockdev and a cachedev
    """

    def __init__(self, blockdevs, added_as):
        """ Initializer.

            :param list of str blockdevs: the blockdevs that would be added in both tiers
            :param _stratisd_constants.BlockDevTiers added_as: whether the action causing the
            error on the cache or data tier
        """
        # pylint: disable=super-init-not-called
        self.blockdevs = blockdevs
        self.added_as = added_as

    def __str__(self):
        if self.added_as == BlockDevTiers.Data:
            already_added = BlockDevTiers.Cache
        else:
            already_added = BlockDevTiers.Data

        return (
            "The resources %s would be added to the %s tier but have already been "
            "added to the %s tier"
            % (
                self.blockdevs,
                BLOCK_DEV_TIER_TO_NAME(self.added_as),
                BLOCK_DEV_TIER_TO_NAME(already_added),
            )
        )


# This exception is only raised in the unlikely event that the introspection
# data contains an unknown interface or that there is a bug in the
# dbus-client-gen library. In either case, these problems will be fixed
# immediately. There is no reason to require coverage for this error.
class StratisCliUnknownInterfaceError(StratisCliRuntimeError):  # pragma: no cover
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


class StratisCliEnvironmentError(StratisCliError):
    """
    Exception that occurs during processing of environment variables.
    """
