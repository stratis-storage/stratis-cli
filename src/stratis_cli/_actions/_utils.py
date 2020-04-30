# Copyright 2020 Red Hat, Inc.
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
Miscellaneous functions.
"""

from .._errors import (
    StratisCliEnginePropertyError,
    StratisCliEnvironmentError,
    StratisCliPropertyNotFoundError,
)


def get_timeout(value):
    """
    Turn an input str or int into a float timeout value.

    :param value: the input str or int
    :type value: str or int
    :raises StratisCliEnvironmentError:
    :returns: float
    """

    maximum_dbus_timeout_ms = 1073741823

    # Ensure the input str is not a float
    if isinstance(value, float):
        raise StratisCliEnvironmentError(
            "The timeout value provided is a float; it should be an integer."
        )

    try:
        timeout_int = int(value)

    except ValueError:
        raise StratisCliEnvironmentError(
            "The timeout value provided is not an integer."
        )

    # Ensure the integer is not too small
    if timeout_int < -1:
        raise StratisCliEnvironmentError(
            "The timeout value provided is smaller than the smallest acceptable value, -1."
        )

    # Ensure the integer is not too large
    if timeout_int > maximum_dbus_timeout_ms:
        raise StratisCliEnvironmentError(
            "The timeout value provided exceeds the largest acceptable value, %s."
            % maximum_dbus_timeout_ms
        )

    # Convert from milliseconds to seconds
    return timeout_int / 1000


def fetch_property(object_type, props, name):
    """
    Get a property fetched through FetchProperties interface

    :param object_type: string representation of object type implementing FetchProperties
    :type object_type: str
    :param props: dictionary of property names mapped to values
    :type props: dict of strs to (bool, object)
    :param name: the name of the property
    :type name: str
    :returns: the object in the dict
    :raises StratisCliPropertyNotFoundError:
    :raises StratisCliEnginePropertyError:
    """
    # Disable coverage for failure of the engine to successfully get a value
    # or for a property not existing for a specified key. We can not force the
    # engine error easily and should not force it these CLI tests. A KeyError
    # can only be raised if there is a bug in the code or if the version of
    # stratisd being run is not compatible with the version of the CLI being
    # tested. We expect to avoid those conditions, and choose not to test for
    # them.
    try:
        (success, variant) = props[name]
        if not success:
            raise StratisCliEnginePropertyError(
                object_type, name, variant
            )  # pragma: no cover
        return variant
    except KeyError:  # pragma: no cover
        raise StratisCliPropertyNotFoundError(object_type, name)
