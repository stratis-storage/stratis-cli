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
Facilities for managing and reporting errors.
"""
import os
import sys

import dbus

from dbus_client_gen import DbusClientMissingPropertyError
from dbus_client_gen import DbusClientMissingSearchPropertiesError
from dbus_client_gen import DbusClientUniqueResultError

from ._actions import BLOCKDEV_INTERFACE
from ._actions import FILESYSTEM_INTERFACE
from ._actions import POOL_INTERFACE

from ._errors import StratisCliEngineError
from ._errors import StratisCliUnknownInterfaceError
from ._errors import StratisCliEnvironmentError

_DBUS_INTERFACE_MSG = (
    "The version of stratis you are running expects a different "
    "D-Bus interface than the one stratisd provides. Most likely "
    "you are running a version that requires a newer version of "
    "stratisd than you are running."
)


# pylint: disable=fixme
# FIXME: remove no coverage pragma when adequate testing for CLI output exists.
def _interface_name_to_common_name(interface_name):  # pragma: no cover
    """
    Maps a D-Bus interface name to the common name that identifies the type
    of stratisd thing that the interface represents.

    :param str interface_name: the interface name
    :returns: a common name
    :rtype: str
    """
    if interface_name == BLOCKDEV_INTERFACE:
        return "block device"

    if interface_name == FILESYSTEM_INTERFACE:
        return "filesystem"

    if interface_name == POOL_INTERFACE:
        return "pool"

    raise StratisCliUnknownInterfaceError(interface_name)


def get_errors(exc):
    """
    Generates a sequence of exceptions starting with exc and following the chain
    of causes.
    """
    while True:
        yield exc
        exc = getattr(exc, "__cause__") or getattr(exc, "__context__")
        if exc is None:
            return


# pylint: disable=too-many-return-statements
def interpret_errors(errors):
    """
    Laboriously add best guesses at the cause of the error, based on
    developer knowledge and possibly further information that is gathered
    in this method.

    :param errors: the chain of errors
    :type errors: list of Exception
    :returns: None if no interpretation found, otherwise str
    """
    # pylint: disable=fixme
    # TODO: This method is extremely rudimentary. It should not be extended
    # using exactly the structure it has now.
    try:
        # Inspect top-most error after StratisCliActionError
        error = errors[1]

        # pylint: disable=fixme
        # FIXME: remove no coverage pragma when adequate testing for CLI
        # output exists.
        if (
            # pylint: disable=bad-continuation
            isinstance(error, DbusClientUniqueResultError)
            and error.result == []
        ):  # pragma: no cover
            fmt_str = "Most likely you specified a %s which does not exist."
            return fmt_str % _interface_name_to_common_name(error.interface_name)

        # These errors can only arise if there is a bug in the way automatically
        # generated code is constructed, or if the introspection data from
        # which the auto-generated code is constructed does not match the
        # daemon interface. This situation is unlikely and difficult to
        # elicit in a test.
        if isinstance(
            # pylint: disable=bad-continuation
            error,
            DbusClientMissingSearchPropertiesError,
        ):  # pragma: no cover
            return _DBUS_INTERFACE_MSG
        if isinstance(error, DbusClientMissingPropertyError):  # pragma: no cover
            return _DBUS_INTERFACE_MSG

        # pylint: disable=fixme
        # FIXME: remove no coverage pragma when adequate testing for CLI
        # output exists.
        if isinstance(error, StratisCliEngineError):  # pragma: no cover
            fmt_str = (
                "stratisd failed to perform the operation that you "
                "requested. It returned the following information via "
                "the D-Bus: %s."
            )
            return fmt_str % error

        if isinstance(error, StratisCliEnvironmentError):
            fmt_str = "%s"
            return fmt_str % error

        # Inspect lowest error
        error = errors[-1]

        # pylint: disable=fixme
        # FIXME: remove no coverage pragma when adequate testing for CLI
        # output exists.
        if (
            # pylint: disable=bad-continuation
            isinstance(error, dbus.exceptions.DBusException)
            and error.get_dbus_name() == "org.freedesktop.DBus.Error.AccessDenied"
        ):  # pragma: no cover
            return "Most likely stratis has insufficient permissions for the action requested."
        # We have observed two causes of this problem. The first is that
        # stratisd is not running at all. The second is that stratisd has not
        # yet established its D-Bus service.
        if (
            # pylint: disable=bad-continuation
            isinstance(error, dbus.exceptions.DBusException)
            and error.get_dbus_name() == "org.freedesktop.DBus.Error.NameHasNoOwner"
        ):
            return "Most likely stratis is unable to connect to the stratisd D-Bus service."

        # The goal is to have an explanation for every error chain. If there is
        # none, then this will rapidly be fixed, so it will be difficult to
        # maintain coverage for this branch.
        return None  # pragma: no cover

    # This indicates that an exception has occurred while an explanation was
    # being constructed. This would be hard to cause, since the code is
    # written in order to make that impossible.
    # pylint: disable=broad-except
    except Exception:  # pragma: no cover
        return None


def handle_error(err):
    """
    Do the right thing with the given error, which may be the head of an error
    chain.

    :param Exception err: an exception
    """

    errors = [error for error in get_errors(err)]

    explanation = interpret_errors(errors)

    # The goal is to have an explanation for every error chain. If there is
    # none, then this will rapidly be fixed, so it will be difficult to
    # maintain coverage for this branch.
    if explanation is None:  # pragma: no cover
        exit_msg = (
            "stratis encountered an unexpected error during execution. "
            "Please report the error and include in your report the stack "
            "trace shown below."
        )
        print(exit_msg, os.linesep, file=sys.stderr, flush=True)
        raise err

    exit_msg = "Execution failed:%s%s" % (os.linesep, explanation)
    sys.exit(exit_msg)
