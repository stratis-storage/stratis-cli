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
from typing import List, Optional

# isort: THIRDPARTY
import dbus

# isort: FIRSTPARTY
from dbus_client_gen import (
    DbusClientMissingPropertyError,
    DbusClientMissingSearchPropertiesError,
    DbusClientUniqueResultError,
)
from dbus_python_client_gen import (
    DPClientGetPropertyContext,
    DPClientInvocationError,
    DPClientMethodCallContext,
    DPClientSetPropertyContext,
)

from ._actions import (
    BLOCKDEV_INTERFACE,
    FILESYSTEM_INTERFACE,
    MANAGER_0_INTERFACE,
    POOL_INTERFACE,
    get_errors,
)
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


def _interface_name_to_common_name(interface_name: str) -> str:
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


def _interpret_errors_0(
    error: dbus.exceptions.DBusException,
) -> Optional[str]:
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

    dbus_name = error.get_dbus_name()

    # The permissions with which stratis-cli makes requests on the D-Bus
    # are controlled by the "stratisd.conf" file. The CLI tests do not
    # control the contents or installation of "stratisd.conf"
    # and therefore, we cannot test this case reliably.
    if dbus_name == "org.freedesktop.DBus.Error.AccessDenied":  # pragma: no cover
        return (
            "Most likely stratis has insufficient permissions for the action requested."
        )

    # We have observed three causes of this problem. The first is that
    # stratisd is not running at all. The second is that stratisd has not
    # yet established its D-Bus service. The third is that stratisd is
    # running with a new major version and is supplying a different name on the
    # D-Bus than stratis is attempting to use. The second and third
    # possibilities are both covered by a single error message.
    if dbus_name in (
        "org.freedesktop.DBus.Error.NameHasNoOwner",
        "org.freedesktop.DBus.Error.ServiceUnknown",
    ):
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

    # The goal is to have an explanation for every type of D-Bus error that
    # is encountered. If there is none, then this will rapidly be fixed, so it
    # will be unnecessary to maintain coverage for this branch.
    return None  # pragma: no cover


def _interpret_errors_1(  # pylint: disable=too-many-return-statements, too-many-branches
    errors: List[BaseException],
) -> Optional[str]:
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
    # elicit in a test. It may arise however, in the case where there
    # is an error producing a property and that property, even although
    # part of the official API, is missing from the GetManagedObjects result.
    if isinstance(
        error,
        (DbusClientMissingSearchPropertiesError, DbusClientMissingPropertyError),
    ):  # pragma: no cover
        if len(errors) > 1:
            maybe_key_error = errors[1]
            if isinstance(maybe_key_error, KeyError):
                prop_key = (
                    maybe_key_error.args[0] if len(maybe_key_error.args) > 0 else ""
                )
                return (
                    f'Property "{prop_key}" belonging to interface '
                    f'"{error.interface_name}" is not in this '
                    "GetManagedObjects result. This could be due to the fact "
                    "that stratisd omitted the property from the "
                    "GetManagedObjects result because there was an error in "
                    "obtaining that value."
                )

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
            f"stratis reported an error in generating a synthetic "
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


def _interpret_errors_2(  # pylint: disable=too-many-return-statements
    errors: List[BaseException],
) -> Optional[str]:
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
            dbus_name = next_error.get_dbus_name()
            dbus_message = next_error.get_dbus_message()
            context = error.context

            if dbus_name == "org.freedesktop.zbus.Error" and isinstance(
                context, DPClientSetPropertyContext
            ):
                return (
                    f"stratisd failed to perform the operation that you "
                    f"requested, because it could not set the D-Bus "
                    f'property "{context.property_name}" belonging to '
                    f'interface "{error.interface_name}" to "{context.value}". '
                    f"It returned the following error: {dbus_message}."
                )

            # We do not test this error, as the only known way to cause it is
            # manipulation of selinux configuration, which is too laborious to
            # bother with at this time.
            if (
                dbus_name == "org.freedesktop.DBus.Error.Disconnected"
            ):  # pragma: no cover
                return (
                    "The D-Bus connection was disconnected during a "
                    "D-Bus interaction. Most likely, your selinux settings "
                    "prohibit that particular D-Bus interaction. The D-Bus "
                    f"service sent the following message: {dbus_message}."
                )

            if dbus_name == "org.freedesktop.DBus.Error.Failed":

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
                        "and the command will succeed if run again. The D-Bus "
                        f"service sent the following message: {dbus_message}."
                    )

                if isinstance(context, DPClientGetPropertyContext):  # pragma: no cover
                    return (
                        f"stratisd failed to perform the operation that you "
                        f"requested, because it could not get the D-Bus "
                        f'property "{context.property_name}" belonging to '
                        f'interface "{error.interface_name}". '
                        f"It returned the following error: {dbus_message}."
                    )

            if dbus_name == "org.freedesktop.DBus.Error.NoReply":
                if (
                    error.interface_name == MANAGER_0_INTERFACE
                    and isinstance(context, DPClientGetPropertyContext)
                    and context.property_name == "Version"
                ):
                    return (
                        "stratis did not send the requested commands to "
                        "stratisd. stratis attempted communication with "
                        "the daemon, stratisd, over the D-Bus, but stratisd "
                        "did not respond in the allowed time. The D-Bus "
                        f"service sent the following message: {dbus_message}."
                    )

                return (
                    "stratis sent the requested commands to stratisd over "
                    "the D-Bus but stratisd did not return the results in "
                    "the allowed time. The D-Bus service sent the following "
                    f"message: {dbus_message}."
                )

    return None  # pragma: no cover


def _interpret_errors(errors: List[BaseException]) -> Optional[str]:
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
        assert len(errors) > 1

        return _interpret_errors_1(errors[1:])

    # This indicates that an exception has occurred while an explanation was
    # being constructed. This would be hard to cause, since the code is
    # written in order to make that impossible.
    # pylint: disable=broad-except
    except Exception:  # pragma: no cover
        return None


def handle_error(err: StratisCliActionError):
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
        print(exit_msg, file=sys.stderr, flush=True)
        raise err

    exit_msg = f"Execution failed:{os.linesep}{explanation}"
    exit_(StratisCliErrorCodes.ERROR, exit_msg)
