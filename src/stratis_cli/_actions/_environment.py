# Copyright 2021 Red Hat, Inc.
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
Environment functions.
"""

from .._errors import StratisCliEnvironmentError


def get_timeout(value):
    """
    Turn an input str or int (milliseconds) into an int timeout value (secs).

    :param value: the input str or int
    :type value: str or int
    :raises StratisCliEnvironmentError:
    :returns: int
    """

    maximum_dbus_timeout_ms = 1073741823

    # Ensure the input str is not a float
    if isinstance(value, float):
        raise StratisCliEnvironmentError(
            "The timeout value provided is a float; it should be an integer."
        )

    try:
        timeout_int = int(value)

    except ValueError as err:
        raise StratisCliEnvironmentError(
            "The timeout value provided is not an integer."
        ) from err

    # Ensure the integer is not too small
    if timeout_int < -1:
        raise StratisCliEnvironmentError(
            "The timeout value provided is smaller than the smallest acceptable value, -1."
        )

    # Ensure the integer is not too large
    if timeout_int > maximum_dbus_timeout_ms:
        raise StratisCliEnvironmentError(
            f"The timeout value provided exceeds the largest acceptable value, "
            f"{maximum_dbus_timeout_ms}."
        )

    # Convert from milliseconds to seconds
    return timeout_int // 1000
