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

MANAGER_SPEC = """
<interface name="org.storage.stratis3.Manager.r0">
    <property access="read" name="Version" type="s">
        <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const" />
    </property>
</interface>
"""


class Purpose(Enum):
    """
    Purpose of class to be created.
    """

    INVOKE = 0  # invoke D-Bus methods
    OBJECT = 1  # represent object in GetManagedObjects result
    SEARCH = 2  # search for object in GEtManagedObjects result


_LOOKUP = {
    "Manager": (
        Purpose.INVOKE,
        lambda: ET.fromstring(SPECS[MANAGER_INTERFACE]),  # nosec B314
        None,
    ),
    "Manager0": (
        Purpose.INVOKE,
        lambda: ET.fromstring(MANAGER_SPEC),  # nosec B314
        None,
    ),
    "ObjectManager": (
        Purpose.INVOKE,
        lambda: ET.fromstring(
            SPECS["org.freedesktop.DBus.ObjectManager"]
        ),  # nosec B314
        None,
    ),
    "Report": (
        Purpose.INVOKE,
        lambda: ET.fromstring(SPECS[REPORT_INTERFACE]),  # nosec B314
        None,
    ),
}


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
        New path method
        """
        rel_paths = [path for path in args[key] if not os.path.isabs(path)]
        assert (
            rel_paths == []
        ), f"Precondition violated: paths {', '.join(rel_paths)} should be absolute"
        return orig_method(proxy, args)

    setattr(method_class, method_name, new_method)


def make_dyn_class(name):
    """
    Dynamically generate a class from introspection specification.

    :param str name: name of class to make
    """
    (purpose, interface_func, klass) = _LOOKUP[name]

    if klass is not None:
        return klass

    assert interface_func is not None

    if purpose is Purpose.INVOKE:  # pragma: no cover
        try:
            klass = make_class(
                name,
                interface_func(),
                TIMEOUT,
            )

            try:
                if name == "Manager":
                    _add_abs_path_assertion(klass, "CreatePool", "devices")
                if name == "Pool":  # pragma: no cover
                    _add_abs_path_assertion(klass, "InitCache", "devices")
                    _add_abs_path_assertion(klass, "AddCacheDevs", "devices")
                    _add_abs_path_assertion(klass, "AddDataDevs", "devices")
            except AttributeError as err:  # pragma: no cover
                # This can only happen if the expected method is missing from
                # the XML spec or code generation has a bug, we will never
                # test for these conditions.
                raise StratisCliGenerationError(
                    "Malformed class definition; could not access a class or "
                    "method in the generated class definition"
                ) from err

        except DPClientGenerationError as err:  # pragma: no cover
            raise StratisCliGenerationError(
                f"Failed to generate class {name} needed for invoking "
                "dbus-python methods"
            ) from err

    # set the function to None since the class has been obtained
    _LOOKUP[name] = (purpose, None, klass)

    return klass
