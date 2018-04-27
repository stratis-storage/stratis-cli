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
    return


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

    sys.exit("Execution failure caused by:%s%s" % (os.linesep, error_msg))
