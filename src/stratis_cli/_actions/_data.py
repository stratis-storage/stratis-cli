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
import xml.etree.ElementTree as ET  # nosec B405
from typing import Callable, Type

# isort: FIRSTPARTY
from dbus_client_gen import (
    DbusClientGenerationError,
    GMOQuery,
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


def _add_abs_path_assertion(klass: Type, method_name: str, key: str) -> None:
    """
    Set method_name of method_klass to a new method which checks that the
    device paths values at key are absolute paths.

    :param klass: the klass to which this metthod belongs
    :param str method_name: the name of the method
    :param str key: the key at which the paths can be found in the arguments
    """
    method_class = getattr(klass, "Methods", None)
    if method_class is None:
        return
    orig_method = getattr(method_class, method_name, None)
    if orig_method is None:
        return

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


class ClassGen:
    """
    Class for constructing introspection-based methods.
    """

    def __init__(
        self,
        interface_name: str,
        dp_class_name: str,
        mo_class_name: str,
    ):
        """
        Initializer.
        """
        self.interface_name = interface_name
        self.dp_class_name = dp_class_name
        self.mo_class_name = mo_class_name
        self._parsed_introspection_data = None
        self._searcher = None
        self._mo = None

    def introspection_data(self) -> ET.Element:
        """
        Parse the introspection data for this interface if not yet parsed.
        """
        if self._parsed_introspection_data is None:
            self._parsed_introspection_data = ET.fromstring(
                SPECS[self.interface_name]
            )  # nosec B314
        return self._parsed_introspection_data

    def mo(self) -> Type:
        """
        Return the managed object class result property getter.
        """
        if self._mo is None:
            try:
                self._mo = managed_object_class(
                    self.mo_class_name, self.introspection_data()
                )
            except DbusClientGenerationError as err:  # pragma: no cover
                raise StratisCliGenerationError(
                    "Failed to generate some class needed for examining D-Bus data"
                ) from err
        return self._mo

    def query_builder(self) -> Callable[..., GMOQuery]:
        """
        Return the query builder
        """
        if self._searcher is None:
            self._searcher = mo_query_builder(self.introspection_data())
        return self._searcher

    def dp_class(
        self,
        *,
        timeout: int = DBUS_TIMEOUT_SECONDS,
    ) -> Type:
        """
        Make a class from a spec with only requested methods and properties.

        Interpret None as meaning include all, [] as meaning include none.
        """
        timeout = get_timeout(os.environ.get("STRATIS_DBUS_TIMEOUT", timeout * 1000))
        spec = self.introspection_data()
        try:
            klass = make_class(self.dp_class_name, spec, timeout=timeout)
            if self.dp_class_name == "Manager":
                _add_abs_path_assertion(klass, "CreatePool", "devices")
            if self.dp_class_name == "Pool":
                _add_abs_path_assertion(klass, "InitCache", "devices")
                _add_abs_path_assertion(klass, "AddCacheDevs", "devices")
                _add_abs_path_assertion(klass, "AddDataDevs", "devices")
            return klass
        except DPClientGenerationError as err:  # pragma: no cover
            raise StratisCliGenerationError(
                "Failed to generate some class needed for invoking dbus-python methods"
            ) from err


BLOCKDEV_GEN = ClassGen(BLOCKDEV_INTERFACE, "Blockdev", "MODev")
FILESYSTEM_GEN = ClassGen(FILESYSTEM_INTERFACE, "Filesystem", "MOFilesystem")
MANAGER0_GEN = ClassGen(MANAGER_0_INTERFACE, "Manager0", "MOManager0")
MANAGER_GEN = ClassGen(MANAGER_INTERFACE, "Manager", "MOManager")
OBJECT_MANAGER_GEN = ClassGen(
    "org.freedesktop.DBus.ObjectManager", "ObjectManager", "MOObjectManager"
)
POOL_GEN = ClassGen(POOL_INTERFACE, "Pool", "MOPool")
REPORT_GEN = ClassGen(REPORT_INTERFACE, "Report", "MOReport")
