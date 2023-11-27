# Copyright 2023 Red Hat, Inc.
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
Dynamic class generation
"""
# isort: STDLIB
import os
import xml.etree.ElementTree as ET  # nosec B405
from enum import Enum

# isort: FIRSTPARTY
from dbus_python_client_gen import DPClientGenerationError, make_class

from .._errors import StratisCliGenerationError
from ._constants import MANAGER_INTERFACE, REPORT_INTERFACE
from ._environment import get_timeout
from ._introspect import SPECS

DBUS_TIMEOUT_SECONDS = 120

TIMEOUT = get_timeout(
    os.environ.get("STRATIS_DBUS_TIMEOUT", DBUS_TIMEOUT_SECONDS * 1000)
)


class ClassKey(Enum):
    """
    Keys for dynamically generated classes.
    """

    MANAGER = ("Manager", MANAGER_INTERFACE)
    OBJECT_MANAGER = ("ObjectManager", "org.freedesktop.DBus.ObjectManager")
    REPORT = ("Report", REPORT_INTERFACE)


def make_dyn_class(key):
    """
    Dynamically generate a class from introspection specification.
    """
    try:
        return make_class(
            key.value[0],
            ET.fromstring(SPECS[key.value[1]]),  # nosec B314
            TIMEOUT,
        )
    except DPClientGenerationError as err:  # pragma: no cover
        raise StratisCliGenerationError(
            "Failed to generate some class needed for invoking dbus-python methods"
        ) from err
