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
import os
import sys
import xml.etree.ElementTree as ET  # nosec B405
from typing import List, Optional, Type

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
    FILESYSTEM_INTERFACE,
    MANAGER_0_INTERFACE,
    MANAGER_INTERFACE,
    POOL_INTERFACE,
    REPORT_INTERFACE,
)
from ._environment import get_timeout
from ._introspect import SPECS

assert hasattr(sys.modules.get("stratis_cli"), "run"), (
    "This module is being loaded too eagerly. Make sure that loading it is "
    "deferred until after the stratis_cli module has been fully loaded."
)

DBUS_TIMEOUT_SECONDS = 120

# Specification for the lowest manager interface supported by the major
# version of stratisd on which this version of the CLI depends.
# This minimal specification includes only the specification for the
# Version property.
SPECS |= (
    {}
    if MANAGER_0_INTERFACE == MANAGER_INTERFACE
    else {
        MANAGER_0_INTERFACE: """
    <interface name="org.storage.stratis3.Manager.r0">
        <property access="read" name="Version" type="s">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const" />
        </property>
    </interface>
    """
    }
)


class DbusClassGen:  # pylint: disable=too-few-public-methods
    """
    Instructions for making a dbus-python class for calling D-Bus methods.
    """

    def __init__(self, name: str, interface_name: str):
        """
        Initializer.
        """
        self.name = name
        self.interface_name = interface_name

    def make_partial_class(
        self,
        *,
        methods: Optional[List[str]] = None,
        properties: Optional[List[str]] = None,
        timeout: int = DBUS_TIMEOUT_SECONDS,  # pylint: disable=redefined-outer-name
    ) -> Type:
        """
        Make a class from a spec with only requested methods and properties.

        Interpret None as meaning include all, [] as meaning include none.
        """
        timeout = get_timeout(os.environ.get("STRATIS_DBUS_TIMEOUT", timeout * 1000))

        spec = ET.fromstring(SPECS[self.interface_name])  # nosec B314

        new_spec = ET.Element(spec.tag, spec.attrib)
        new_spec.extend(
            [
                child
                for child in spec
                if child.tag == "method"
                and (methods is None or child.get("name") in methods)
            ]
        )
        new_spec.extend(
            [
                child
                for child in spec
                if child.tag == "property"
                and (properties is None or child.get("name") in properties)
            ]
        )
        return make_class(self.name, new_spec, timeout=timeout)


REPORT_GEN = DbusClassGen("Report", REPORT_INTERFACE)
FILESYSTEM_GEN = DbusClassGen("Filesystem", FILESYSTEM_INTERFACE)
MANAGER_GEN = DbusClassGen("Manager", MANAGER_INTERFACE)
POOL_GEN = DbusClassGen("Pool", POOL_INTERFACE)

try:
    # pylint: disable=invalid-name

    timeout = get_timeout(
        os.environ.get("STRATIS_DBUS_TIMEOUT", DBUS_TIMEOUT_SECONDS * 1000)
    )

    filesystem_spec = ET.fromstring(SPECS[FILESYSTEM_INTERFACE])  # nosec B314
    MOFilesystem = managed_object_class("MOFilesystem", filesystem_spec)
    filesystems = mo_query_builder(filesystem_spec)

    pool_spec = ET.fromstring(SPECS[POOL_INTERFACE])  # nosec B314
    MOPool = managed_object_class("MOPool", pool_spec)
    pools = mo_query_builder(pool_spec)

    blockdev_spec = ET.fromstring(SPECS[BLOCKDEV_INTERFACE])  # nosec B314
    MODev = managed_object_class("MODev", blockdev_spec)
    devs = mo_query_builder(blockdev_spec)

    ObjectManager = make_class(
        "ObjectManager",
        ET.fromstring(SPECS["org.freedesktop.DBus.ObjectManager"]),  # nosec B314
        timeout,
    )

    Manager0 = make_class(
        "Manager0", ET.fromstring(SPECS[MANAGER_0_INTERFACE]), timeout  # nosec B314
    )

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


def _add_abs_path_assertion(klass, method_name, key):
    """
    Set method_name of method_klass to a new method which checks that the
    device paths values at key are absolute paths.

    :param klass: the klass to which this metthod belongs
    :param str method_name: the name of the method
    :param str key: the key at which the paths can be found in the arguments
    """
    method_class = getattr(klass, "Methods")
    orig_method = getattr(method_class, method_name)

    def new_method(proxy, args):
        """
        New CreatePool method
        """
        rel_paths = [path for path in args[key] if not os.path.isabs(path)]
        assert (
            rel_paths == []
        ), f"Precondition violated: paths {', '.join(rel_paths)} should be absolute"
        return orig_method(proxy, args)

    setattr(method_class, method_name, new_method)


try:
    # _add_abs_path_assertion(Manager, "CreatePool", "devices")
    # _add_abs_path_assertion(Pool, "InitCache", "devices")
    # _add_abs_path_assertion(Pool, "AddCacheDevs", "devices")
    # _add_abs_path_assertion(Pool, "AddDataDevs", "devices")
    pass

except AttributeError as err:  # pragma: no cover
    # This can only happen if the expected method is missing from the XML spec
    # or code generation has a bug, we will never test for these conditions.
    raise StratisCliGenerationError(
        "Malformed class definition; could not access a class or method in "
        "the generated class definition"
    ) from err
