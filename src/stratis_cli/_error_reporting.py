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

from dbus_client_gen import DbusClientMissingInterfaceError
from dbus_client_gen import DbusClientMissingPropertyError
from dbus_client_gen import DbusClientMissingSearchPropertiesError
from dbus_client_gen import DbusClientUniqueResultError
from dbus_client_gen import DbusClientUnknownSearchPropertiesError

from ._actions import interface_name_to_common_name

from ._errors import StratisCliStratisdVersionError

_DBUS_INTERFACE_MSG = (
    "The version of stratis you are running expects a different "
    "D-Bus interface than the one stratisd provides. Most likely "
    "you are running a version that requires a newer version of "
    "stratisd than you are running.")

_STRATIS_CLI_BUG_MSG = ("Most likely there is a bug in stratis, the program "
                        "you are running.")


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


def get_error_msgs(errors):
    """
    Generates messages from a sequence of errors. Omits empty messages
    """
    for error in errors:
        if isinstance(error, dbus.exceptions.DBusException):
            error_str = error.get_dbus_message()
        else:
            error_str = str(error)
        if error_str is not None and error_str != "":
            yield error_str


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
        if isinstance(error, AttributeError):
            import traceback
            frame = traceback.extract_tb(error.__traceback__)[-1]
            fmt_str = (
                "Most likely there is an error in the source at line %d "
                "in file %s. The text of the line is \"%s\".")
            return fmt_str % (frame.lineno, frame.filename, frame.line)

        if isinstance(error,
                      DbusClientUniqueResultError) and error.result == []:
            fmt_str = "Most likely you specified a %s which does not exist."
            return fmt_str % interface_name_to_common_name(
                error.interface_name)

        if isinstance(error, DbusClientUnknownSearchPropertiesError):
            return _STRATIS_CLI_BUG_MSG
        if isinstance(error, DbusClientMissingSearchPropertiesError):
            return _DBUS_INTERFACE_MSG
        if isinstance(error, DbusClientMissingInterfaceError):
            return _STRATIS_CLI_BUG_MSG
        if isinstance(error, DbusClientMissingPropertyError):
            return _DBUS_INTERFACE_MSG

        if isinstance(error, StratisCliStratisdVersionError):
            fmt_str = ("%s. stratis can execute only the subset of its "
                       "commands that do not require stratisd.")
            return fmt_str % (error, )

        # Inspect lowest error
        error = errors[-1]
        if isinstance(error, dbus.exceptions.DBusException) and \
            error.get_dbus_name() == \
            'org.freedesktop.DBus.Error.AccessDenied':
            return "Most likely stratis has insufficient permissions for the action requested."
        # We have observed two causes of this problem. The first is that
        # stratisd is not running at all. The second is that stratisd has not
        # yet established its D-Bus service.
        if isinstance(error, dbus.exceptions.DBusException) and \
            error.get_dbus_name() == \
            'org.freedesktop.DBus.Error.NameHasNoOwner':
            return "Most likely stratis is unable to connect to the stratisd D-Bus service."

        return None
    # pylint: disable=broad-except
    except Exception:
        return None


def generate_error_message(errors):
    """
    Generate an error message from the given errors.

    :param errors: a list of exceptions
    :type errors: list of Exception

    :returns: str

    Precondition: len(errors) > 0
    """
    # Skip message from first error, which is StratisCliActionError.
    # This error just tells what the command line arguments were and what
    # the resulting parser namespace was, which is probably not interesting
    # to the user.
    error_msgs = [msg for msg in get_error_msgs(errors[1:])]
    if error_msgs == []:
        # It is unlikely that, within the whole chain of errors, there
        # will be no message that is not an empty string. If there is
        # there is some program error, so just raise the exception.
        raise errors[0]

    return ("%s    which in turn caused:%s" % (os.linesep, os.linesep)).join(
        reversed(error_msgs))


def handle_error(err):
    """
    Do the right thing with the given error, which may be the head of an error
    chain.

    :param Exception err: an exception
    """

    errors = [error for error in get_errors(err)]

    error_msg = generate_error_message(errors)

    explanation = interpret_errors(errors)

    exit_msg = "Execution failure caused by:%s%s" % (os.linesep, error_msg) + \
            ("" if explanation is None else "%s%s%s" % (os.linesep, os.linesep, explanation))

    sys.exit(exit_msg)
