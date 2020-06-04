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
# isort: STDLIB
import os
import sys

# isort: THIRDPARTY
import dbus

# isort: FIRSTPARTY
from dbus_client_gen import (
    DbusClientMissingPropertyError,
    DbusClientMissingSearchPropertiesError,
    DbusClientUniqueResultError,
)

from ._actions import BLOCKDEV_INTERFACE, FILESYSTEM_INTERFACE, POOL_INTERFACE
from ._errors import (
    StratisCliActionError,
    StratisCliAggregateError,
    StratisCliEngineError,
    StratisCliEnginePropertyError,
    StratisCliIncoherenceError,
    StratisCliStratisdVersionError,
    StratisCliUnknownInterfaceError,
    StratisCliUserError,
)
from ._exit import StratisCliErrorCodes, exit_

_DBUS_INTERFACE_MSG = (
    "The version of stratis you are running expects a different "
    "D-Bus interface than the one stratisd provides. Most likely "
    "you are running a version that requires a newer version of "
    "stratisd than you are running."
)


def _interface_name_to_common_name(interface_name):
    """
    Maps a D-Bus interface name to the common name that identifies the type
    of stratisd thing that the interface represents.

    :param str interface_name: the interface name
    :returns: a common name
    :rtype: str
    """
    # There is no action which specifies a block device once it has been
    # added to a pool. Consequently, we cannot test that a non-existent block
    # device has been specified. In the future, if such an action is created,
    # this no cover may be removed.
    if interface_name == BLOCKDEV_INTERFACE:  # pragma: no cover
        return "block device"

    if interface_name == FILESYSTEM_INTERFACE:
        return "filesystem"

    if interface_name == POOL_INTERFACE:
        return "pool"

    # This is a permanent no cover. There should never be an unknown interface.
    raise StratisCliUnknownInterfaceError(interface_name)  # pragma: no cover


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


def _interpret_errors_0(error):
    """
    Handle match on SCAE .*  DBE
      where:
         SCAE is StratisCliActionError
         DBE is dbus.exceptions.DBusException

    :param error: a specific error
    :type error: dbus.exceptions.DBusException
    :returns: the interpretation of the error if found, otherwise None
    :rtype: None or str
    """

    # The permissions with which stratis-cli makes requests on the D-Bus
    # are controlled by the "stratisd.conf" file. The CLI tests do not
    # control the contents or installation of "stratisd.conf"
    # and therefore, we cannot test this case reliably.
    if (
        # pylint: disable=bad-continuation
        error.get_dbus_name()
        == "org.freedesktop.DBus.Error.AccessDenied"
    ):  # pragma: no cover
        return (
            "Most likely stratis has insufficient permissions for the action requested."
        )

    # We have observed two causes of this problem. The first is that
    # stratisd is not running at all. The second is that stratisd has not
    # yet established its D-Bus service.
    if error.get_dbus_name() == "org.freedesktop.DBus.Error.NameHasNoOwner":
        return "Most likely stratis is unable to connect to the stratisd D-Bus service."

    # Due to the uncertain behavior with which libdbus
    # treats a timeout value of 0, it proves difficult to test this case,
    # as seen here: https://github.com/stratis-storage/stratis-cli/pull/476
    # Additional information may be found in the issue filed against libdbus
    # here: https://gitlab.freedesktop.org/dbus/dbus/issues/293
    if (
        # pylint: disable=bad-continuation
        error.get_dbus_name()
        == "org.freedesktop.DBus.Error.NoReply"
    ):  # pragma: no cover
        return (
            "stratis attempted communication with the daemon, stratisd, "
            "over the D-Bus, but stratisd did not respond in the allowed time."
        )

    # The goal is to have an explanation for every type of D-Bus error that
    # is encountered. If there is none, then this will rapidly be fixed, so it
    # will be unnecessary to maintain coverage for this branch.
    return None  # pragma: no cover


def _interpret_errors_1(errors):  # pylint: disable=too-many-return-statements
    """
    Interpret the subchain of errors after the first error.

    :param errors: the chain of errors
    :type errors: list of Exception
    :returns: None if no interpretation found, otherwise str
    """
    error = errors[0]

    if (
        # pylint: disable=bad-continuation
        isinstance(error, DbusClientUniqueResultError)
        and error.result == []
    ):
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
        (DbusClientMissingSearchPropertiesError, DbusClientMissingPropertyError),
    ):  # pragma: no cover
        return _DBUS_INTERFACE_MSG

    if isinstance(error, StratisCliEngineError):
        fmt_str = (
            "stratisd failed to perform the operation that you "
            "requested. It returned the following information via "
            "the D-Bus: %s."
        )
        return fmt_str % error

    # This should arise only if the engine encounters an error while
    # obtaining a property. Therefore, it is not tested.
    if isinstance(error, StratisCliEnginePropertyError):  # pragma: no cover
        return str(error)

    if isinstance(error, StratisCliUserError):
        fmt_str = "It appears that you issued an unintended command: %s"
        return fmt_str % error

    # The only situation in which an AggregateError can be raised is if there
    # is a problem activating devcies, but the sim engine does not simulate
    # activation of locked devices.
    if isinstance(error, StratisCliAggregateError):  # pragma: no cover
        fmt_str = "An iterative command generated one or more errors: %s"
        return fmt_str % error

    if isinstance(error, StratisCliStratisdVersionError):
        fmt_str = (
            "%s. stratis can execute only the subset of its "
            "commands that do not require stratisd."
        )
        return fmt_str % error

    # An incoherence error should be pretty untestable. It can arise
    # * in the case of a stratisd bug. We would expect to fix that very
    # soon, so should not have a test in that case.
    # * in the case where another client of stratisd is running and alters
    # state while a command is being executed. This could be tested for,
    # but only with considerable difficulty, so we choose not to test.
    if isinstance(error, StratisCliIncoherenceError):  # pragma: no cover
        fmt_str = (
            "stratisd reported that it did not execute every action "
            "that it would have been expected to execute as a result "
            "of the command that you requested: %s"
        )
        return fmt_str % error

    # Inspect lowest error
    error = errors[-1]

    if isinstance(error, dbus.exceptions.DBusException):
        explanation = _interpret_errors_0(error)
        if explanation is not None:
            return explanation

    # The goal is to have an explanation for every error chain. If there is
    # none, then this will rapidly be fixed, so it will be difficult to
    # maintain coverage for this branch.
    return None  # pragma: no cover


def _interpret_errors(errors):
    """
    Laboriously add best guesses at the cause of the error, based on
    developer knowledge and possibly further information that is gathered
    in this method.

    Precondition: Every error chain starts with a StratisCliActionError

    :param errors: the chain of errors
    :type errors: list of Exception
    :returns: None if no interpretation found, otherwise str
    """
    try:
        assert isinstance(errors[0], StratisCliActionError)

        return _interpret_errors_1(errors[1:])

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

    errors = list(get_errors(err))

    explanation = _interpret_errors(errors)

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
    exit_(StratisCliErrorCodes.ERROR, exit_msg)
