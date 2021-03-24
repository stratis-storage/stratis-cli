# Copyright 2017 Red Hat, Inc.
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
XML interface specifications.
"""
# isort: STDLIB
import sys
import xml.etree.ElementTree as ET
from os import environ

# isort: FIRSTPARTY
from dbus_client_gen import (
    DbusClientGenerationError,
    managed_object_class,
    mo_query_builder,
)
from dbus_python_client_gen import DPClientGenerationError, make_class

from .._errors import StratisCliGenerationError
from ._constants import (
    BLOCKDEV_INTERFACE,
    FETCH_PROPERTIES_INTERFACE,
    FILESYSTEM_INTERFACE,
    MANAGER_INTERFACE,
    POOL_INTERFACE,
    REPORT_INTERFACE,
)
from ._introspect import SPECS
from ._utils import get_timeout

assert hasattr(sys.modules.get("stratis_cli"), "run"), (
    "This module is being loaded too eagerly. Make sure that loading it is "
    "deferred until after the stratis_cli module has been fully loaded."
)

DBUS_TIMEOUT_SECONDS = 120


try:
    # pylint: disable=invalid-name

    timeout = get_timeout(
        environ.get("STRATIS_DBUS_TIMEOUT", DBUS_TIMEOUT_SECONDS * 1000)
    )

    fetch_properties_spec = ET.fromstring(SPECS[FETCH_PROPERTIES_INTERFACE])
    FetchProperties = make_class("FetchProperties", fetch_properties_spec, timeout)

    report_spec = ET.fromstring(SPECS[REPORT_INTERFACE])
    Report = make_class("Report", report_spec, timeout)

    filesystem_spec = ET.fromstring(SPECS[FILESYSTEM_INTERFACE])
    Filesystem = make_class("Filesystem", filesystem_spec, timeout)
    MOFilesystem = managed_object_class("MOFilesystem", filesystem_spec)
    filesystems = mo_query_builder(filesystem_spec)

    pool_spec = ET.fromstring(SPECS[POOL_INTERFACE])
    Pool = make_class("Pool", pool_spec, timeout)
    MOPool = managed_object_class("MOPool", pool_spec)
    pools = mo_query_builder(pool_spec)

    blockdev_spec = ET.fromstring(SPECS[BLOCKDEV_INTERFACE])
    MODev = managed_object_class("MODev", blockdev_spec)
    devs = mo_query_builder(blockdev_spec)

    Manager = make_class("Manager", ET.fromstring(SPECS[MANAGER_INTERFACE]), timeout)

    ObjectManager = make_class(
        "ObjectManager",
        ET.fromstring(SPECS["org.freedesktop.DBus.ObjectManager"]),
        timeout,
    )

    # Specification for the lowest manager interface supported by the major
    # version of stratisd on which this version of the CLI depends.
    # This minimal specification includes only the specification for the
    # Version property.
    manager_spec = """
    <interface name="org.storage.stratis2.Manager">
        <property access="read" name="Version" type="s">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const" />
        </property>
    </interface>
    """
    Manager0 = make_class("Manager0", ET.fromstring(manager_spec), timeout)

# Do not expect to get coverage on Generation errors.
# These can only occurs if the XML data in _SPECS is ill-formed; we have
# complete control over that data and can expect it to be valid.
except DPClientGenerationError as err:  # pragma: no cover
    raise StratisCliGenerationError(
        "Failed to generate some class needed for invoking dbus-python methods"
    ) from err
except DbusClientGenerationError as err:  # pragma: no cover
    raise StratisCliGenerationError(
        "Failed to generate some class needed for examining D-Bus data"
    ) from err
