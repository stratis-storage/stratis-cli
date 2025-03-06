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
Error hierarchy for stratis cli.
"""

from ._stratisd_constants import BlockDevTiers, StratisdErrors


class StratisCliError(Exception):
    """
    Top-level stratis cli error.
    """


class StratisCliRuntimeError(StratisCliError):
    """
    Exception raised while an action is being performed and as a result of
    the requested action.
    """


class StratisCliUserError(StratisCliRuntimeError):
    """
    Exception raised as a result of a user error.
    """


class StratisCliNoDeviceSizeChangeError(StratisCliUserError):
    """
    Exception raised when the user requests to extend a pool to include new
    space on data devices, but there isn't any.
    """

    def __init__(self):  # pylint: disable=super-init-not-called
        """
        Initializer.
        """

    def __str__(self):
        return (
            "None of the pool's devices seems to have increased in size; the "
            "pool's allocatable space would not be changed."
        )


class StratisCliNoPropertyChangeError(StratisCliUserError):
    """
    Raised when the user requests that a property be changed to its existing
    value.
    """


class StratisCliResourceNotFoundError(StratisCliUserError):
    """
    Raised if a request was made to stratisd to update a resource
    that was expected to exist but was not found.
    """

    def __init__(self, command, resource):
        """
        Initializer.

        :param str command: the executed command
        :param str resource: the target resource
        """
        # pylint: disable=super-init-not-called
        self.command = command
        self.resource = resource

    def __str__(self):
        return (
            f"Command '{self.command}' assumes that resource '{self.resource}' "
            f"exists but it was not found."
        )


class StratisCliPartialChangeError(StratisCliUserError):
    """
    Raised if a request made of stratisd must result in a partial or no change
    since some or all of the post-condition for the request already holds.

    Invariant: self.unchanged_resources != frozenset()
    """

    def __init__(self, command, changed_resources, unchanged_resources):
        """
        Initializer.

        :param str command: the command run that caused the error
        :param changed_resources: the target resources that would change
        :type changed_resources: frozenset of str
        :param unchanged_resources: the target resources that would not change
        :type unchanged_resources: frozenset of str

        Precondition: unchanged_resources != frozenset()
        """
        # pylint: disable=super-init-not-called
        self.command = command
        self.changed_resources = changed_resources
        self.unchanged_resources = unchanged_resources

    def __str__(self):
        if len(self.unchanged_resources) > 1:
            msg = (
                f"The '{self.command}' action has no effect for resources "
                f"{list(self.unchanged_resources)}"
            )
        else:
            msg = (
                f"The '{self.command}' action has no effect for resource "
                f"{list(self.unchanged_resources)[0]}"
            )

        if self.changed_resources != frozenset():
            if len(self.changed_resources) > 1:
                msg += f" but does for resources {list(self.changed_resources)}"
            else:
                msg += f" but does for resource {list(self.changed_resources)[0]}"

        return msg


class StratisCliNoChangeError(StratisCliPartialChangeError):
    """
    Raised if a request made of stratisd must result in no change since the
    post-condition of the request is already entirely satisfied. This is
    a special case of StratisCliPartialChangeError, where the change requested
    is so simple that it can only succeed or fail.
    """

    def __init__(self, command, resource):
        """
        Initializer.

        :param str command: the executed command
        :param str resource: the target resource
        """
        StratisCliPartialChangeError.__init__(
            self, command, frozenset(), frozenset([resource])
        )


class StratisCliNameConflictError(StratisCliUserError):
    """
    Raised if an item of the same name already exists.
    """

    def __init__(self, object_type, name):
        """
        Initializer.

        :param str object_type: the type of the object, pool, filesystem, etc.
        :param str name: the conflicting name
        """
        # pylint: disable=super-init-not-called
        self.object_type = object_type
        self.name = name

    def __str__(self):
        return f"A {self.object_type} named {self.name} already exists"


class StratisCliIncoherenceError(StratisCliRuntimeError):
    """
    Raised if there was a disagreement about state between the CLI
    and the daemon. This can happen if the information derived from
    the GetManagedObjects() result does not correspond with the daemon's
    state. This is a very unlikely event, but could occur if two processes
    were issuing instructions to stratisd at the same time.
    """


class StratisCliSynthUeventError(StratisCliRuntimeError):
    """
    Raised if there was an error during a synthetic udev event generation.
    """


class StratisCliInUseError(StratisCliUserError):
    """
    Base class for if a request made of stratisd must result in a device being
    included in both data and cache tiers or in the same tier of two different
    pools.
    """


class StratisCliInUseOtherTierError(StratisCliInUseError):
    """
    Raised if a request made of stratisd must result in a device being
    included in both data and cache tiers.
    """

    def __init__(self, pools_to_blockdevs, added_as):
        """
        Initializer.

        :param pools_to_blockdevs: pools mapped to the blockdevs they own
        :type pools_to_blockdevs: dict of str * frozenset of str
        :param added_as: what tier the devices were to be added to
        :type added_as: _stratisd_constants.BlockDevTiers

        Precondition: pools_to_blockdevs != {}
        Precondition: all frozenset of str in pools_to_blockdevs have at least one item
        """
        # pylint: disable=super-init-not-called
        self.pools_to_blockdevs = pools_to_blockdevs
        self.added_as = added_as

    def __str__(self):
        (target_blockdev_tier, already_blockdev_tier) = (
            str(self.added_as),
            str(
                BlockDevTiers.DATA
                if self.added_as == BlockDevTiers.CACHE
                else BlockDevTiers.CACHE
            ),
        )

        msg = (
            f"At least one of the provided devices is already owned by an "
            f"existing pool's {already_blockdev_tier} tier"
        )

        for pool_name, blockdevs in self.pools_to_blockdevs.items():
            if len(blockdevs) > 1:
                msg += (
                    f"; devices {list(blockdevs)} would be added to the {target_blockdev_tier} "
                    f"tier but are already in use in the {already_blockdev_tier} tier "
                    f"of pool {pool_name}"
                )
            else:
                msg += (
                    f"; device {list(blockdevs)[0]} would be added to the {target_blockdev_tier} "
                    f"tier but is already in use in the {already_blockdev_tier} tier "
                    f"of pool {pool_name}"
                )

        return msg


class StratisCliInUseSameTierError(StratisCliInUseError):
    """
    Raised if a request made of stratisd must result in a device being
    included in the same tier in two different pools.
    """

    def __init__(self, pools_to_blockdevs, added_as):
        """
        Initializer.

        :param pools_to_blockdevs: pools mapped to the blockdevs they own
        :type pools_to_blockdevs: dict of str * frozenset of str
        :param added_as: what tier the devices were to be added to
        :type added_as: _stratisd_constants.BlockDevTiers

        Precondition: pools_to_blockdevs != {}
        Precondition: all frozenset of str in pools_to_blockdevs have at least one item
        """
        # pylint: disable=super-init-not-called
        self.pools_to_blockdevs = pools_to_blockdevs
        self.added_as = added_as

    def __str__(self):
        blockdev_tier = str(self.added_as)

        msg = (
            f"At least one of the provided devices is already owned by an "
            f"existing pool's {blockdev_tier} tier"
        )

        for pool_name, blockdevs in self.pools_to_blockdevs.items():
            if len(blockdevs) > 1:
                msg += (
                    f"; devices {list(blockdevs)} would be added to the {blockdev_tier} tier "
                    f"but are already in use in the {blockdev_tier} tier of pool {pool_name}"
                )
            else:
                msg += (
                    f"; device {list(blockdevs)[0]} would be added to the {blockdev_tier} tier "
                    f"but is already in use in the {blockdev_tier} tier of pool {pool_name}"
                )

        return msg


class StratisCliKeyfileNotFoundError(StratisCliUserError):
    """
    Raised if the user specified a keyfile which could not be found when
    setting or unsetting a key.
    """

    def __init__(self, keyfile_path):
        """
        Initializer.

        :param str keyfile_path: the unfound path
        """
        # pylint: disable=super-init-not-called
        self.keyfile_path = keyfile_path

    def __str__(self):
        return f'There is no keyfile at the path "{self.keyfile_path}"'


class StratisCliUnknownInterfaceError(StratisCliRuntimeError):
    """
    Error raised when code encounters an unexpected D-Bus interface name.
    """

    def __init__(self, interface_name):
        """
        Initializer.

        :param str interface_name: the unexpected interface name
        """
        # pylint: disable=super-init-not-called
        self._interface_name = interface_name

    def __str__(self):
        return f"unexpected interface name {self._interface_name}"


class StratisCliEngineError(StratisCliRuntimeError):
    """
    Raised if there was a failure due to an error in stratisd's engine.
    """

    def __init__(self, rc, message):
        """
        Initializer.

        :param rc int: the error code returned by the engine
        :param str message: whatever message accompanied the error code
        """
        # pylint: disable=super-init-not-called
        try:
            self.error_code = StratisdErrors(rc)
        except ValueError:
            self.error_code = None

        self.message = message

    def __str__(self):
        error_code_str = "???" if self.error_code is None else str(self.error_code)
        return f"{error_code_str}: {self.message}"


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


class StratisCliStratisdVersionError(StratisCliRuntimeError):
    """
    Raised if stratisd version does not meet CLI version requirements.
    """

    def __init__(self, actual_version, minimum_version, maximum_version):
        """
        Initializer.
        :param tuple actual_version: stratisd's actual version
        :param tuple minimum_version: the minimum version required
        :param tuple maximum_version: the maximum version allowed
        """
        # pylint: disable=super-init-not-called
        self.actual_version = actual_version
        self.minimum_version = minimum_version
        self.maximum_version = maximum_version

    def __str__(self):
        fmt_str = (
            "stratisd version %s does not meet stratis version "
            "requirements; the version must be at least %s and no more "
            "than %s"
        )
        return fmt_str % (
            self.actual_version,
            self.minimum_version,
            self.maximum_version,
        )


class StratisCliPassphraseMismatchError(StratisCliUserError):
    """
    Raised if the user specified passphrase did not match
    the verified passphrase.
    """

    def __str__(self):
        return "Passphrases do not match"


class StratisCliPassphraseEmptyError(StratisCliUserError):
    """
    Raised if the user specified passphrase was empty.
    """

    def __str__(self):
        return "Passphrase is empty"


class StratisCliInvalidCommandLineOptionValue(StratisCliUserError):
    """
    Raised if the user passed an invalid option that cannot be checked at
    parse time.
    """

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
