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
from dbus_python_client_gen import (
    DPClientInvocationError,
    DPClientMethodCallContext,
    DPClientSetPropertyContext,
)

from ._actions import BLOCKDEV_INTERFACE, FILESYSTEM_INTERFACE, POOL_INTERFACE
from ._errors import (
    StratisCliActionError,
    StratisCliEngineError,
    StratisCliIncoherenceError,
    StratisCliStratisdVersionError,
    StratisCliSynthUeventError,
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
        error.get_dbus_name() == "org.freedesktop.DBus.Error.AccessDenied"
    ):  # pragma: no cover
        return (
            "Most likely stratis has insufficient permissions for the action requested."
        )

    # We have observed three causes of this problem. The first is that
    # stratisd is not running at all. The second is that stratisd has not
    # yet established its D-Bus service. The third is that stratisd is
    # running with a new major version and is supplying a different name on the
    # D-Bus than stratis is attempting to use. The second and third
    # possibilities are both covered by a single error message.
    if error.get_dbus_name() == "org.freedesktop.DBus.Error.NameHasNoOwner":
        try:
            # pylint: disable=import-outside-toplevel
            # isort: THIRDPARTY
            import psutil

            for proc in psutil.process_iter():
                try:
                    if proc.name() == "stratisd":  # pragma: no cover
                        return (
                            "Most likely stratis is unable to connect to the "
                            "stratisd D-Bus service."
                        )
                except psutil.NoSuchProcess:  # pragma: no cover
                    pass

            return "It appears that there is no stratisd process running."

        except ImportError:  # pragma: no cover
            return "Most likely there is no stratisd process running."

    # Due to the uncertain behavior with which libdbus
    # treats a timeout value of 0, it proves difficult to test this case,
    # as seen here: https://github.com/stratis-storage/stratis-cli/pull/476
    # Additional information may be found in the issue filed against libdbus
    # here: https://gitlab.freedesktop.org/dbus/dbus/issues/293
    if (
        error.get_dbus_name() == "org.freedesktop.DBus.Error.NoReply"
    ):  # pragma: no cover
        return (
            "stratis attempted communication with the daemon, stratisd, "
            "over the D-Bus, but stratisd did not respond in the allowed time."
        )

    # The goal is to have an explanation for every type of D-Bus error that
    # is encountered. If there is none, then this will rapidly be fixed, so it
    # will be unnecessary to maintain coverage for this branch.
    return None  # pragma: no cover


def _interpret_errors_1(
    errors,
):  # pylint: disable=too-many-return-statements, too-many-branches
    """
    Interpret the subchain of errors after the first error.

    :param errors: the chain of errors
    :type errors: list of Exception
    :returns: None if no interpretation found, otherwise str
    """
    error = errors[0]

    if isinstance(error, DbusClientUniqueResultError) and error.result == []:
        return (
            f"Most likely you specified a "
            f"{_interface_name_to_common_name(error.interface_name)} "
            f"which does not exist."
        )

    # These errors can only arise if there is a bug in the way automatically
    # generated code is constructed, or if the introspection data from
    # which the auto-generated code is constructed does not match the
    # daemon interface. This situation is unlikely and difficult to
    # elicit in a test.
    if isinstance(
        error,
        (DbusClientMissingSearchPropertiesError, DbusClientMissingPropertyError),
    ):  # pragma: no cover
        return _DBUS_INTERFACE_MSG

    if isinstance(error, StratisCliEngineError):
        return (
            f"stratisd failed to perform the operation that you "
            f"requested. It returned the following information via "
            f"the D-Bus: {error}."
        )

    if isinstance(error, StratisCliUserError):
        return f"It appears that you issued an unintended command: {error}"

    if isinstance(error, StratisCliStratisdVersionError):
        return (
            f"{error}. stratis can execute only the subset of its "
            f"commands that do not require stratisd."
        )

    # An incoherence error should be pretty untestable. It can arise
    # * in the case of a stratisd bug. We would expect to fix that very
    # soon, so should not have a test in that case.
    # * in the case where another client of stratisd is running and alters
    # state while a command is being executed. This could be tested for,
    # but only with considerable difficulty, so we choose not to test.
    if isinstance(error, StratisCliIncoherenceError):  # pragma: no cover
        return (
            f"stratisd reported that it did not execute every action "
            f"that it would have been expected to execute as a result "
            f"of the command that you requested: {error}"
        )

    if isinstance(error, StratisCliSynthUeventError):
        return (
            f"stratis reported an error in generating a synethetic "
            f"udev event: {error}"
        )  # pragma: no cover

    # Some method calls may have an assignable underlying cause.
    # At present, automated testing of any of these assignable causes is
    # too laborious to justify.
    if isinstance(error, DPClientInvocationError):  # pragma: no cover
        explanation = _interpret_errors_2(errors)
        if explanation is not None:
            return explanation

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


def _interpret_errors_2(errors):
    """
    Interpret the error when it is known that the first error is a
    DPClientInvocationError

    :param errors: the chain of errors
    :type errors: list of Exception
    :returns: None if no interpretation found, otherwise str
    """
    error = errors[0]

    assert isinstance(error, DPClientInvocationError)

    if len(errors) > 1:
        next_error = errors[1]
        if isinstance(next_error, dbus.exceptions.DBusException):
            # We do not test this error, as the only known way to cause it is
            # manipulation of selinux configuration, which is too laborious to
            # bother with at this time.
            if (
                next_error.get_dbus_name() == "org.freedesktop.DBus.Error.Disconnected"
            ):  # pragma: no cover
                return (
                    "The D-Bus connection was disconnected during a "
                    "D-Bus interaction. Most likely, your selinux settings "
                    "prohibit that particular D-Bus interaction."
                )

            if next_error.get_dbus_name() == "org.freedesktop.DBus.Error.Failed":
                context = error.context

                # We do not test this error, as the only known way to cause it
                # is to spam the daemon with a succession of mutating commands
                # from separate processes. The circumstances that cause this
                # exception to be raised are a call to GetManagedObjects() that
                # is initiated while a call that removes a filesystem or pool
                # is in progress. In that case, the GetManagedObjects() call
                # may process object paths that have not yet been removed and
                # may encounter an error when calculating the object properties
                # since the engine no longer has any record of the filesystem
                # or pool.
                if (
                    error.interface_name == "org.freedesktop.DBus.ObjectManager"
                    and isinstance(context, DPClientMethodCallContext)
                    and context.method_name == "GetManagedObjects"
                ):  # pragma: no cover
                    return (
                        "A D-Bus method failed during execution of the "
                        "selected command. Most likely, the failure was due "
                        "to a transient inconsistency in the D-Bus interface "
                        "and the command will succeed if run again."
                    )

                if isinstance(context, DPClientSetPropertyContext):
                    return (
                        f"stratisd failed to perform the operation that you "
                        f"requested, because it could not set the D-Bus "
                        f'property "{context.property_name}" belonging to '
                        f'interface "{error.interface_name}" to "{context.value}". '
                        f"It returned the following error: "
                        f"{next_error.get_dbus_message()}."
                    )

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

    exit_msg = f"Execution failed:{os.linesep}{explanation}"
    exit_(StratisCliErrorCodes.ERROR, exit_msg)
