# Copyright 2025 Red Hat, Inc.
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
Test 'long_running_operation'.
"""

# isort: STDLIB
import unittest

# isort: THIRDPARTY
import dbus

# isort: FIRSTPARTY
from dbus_python_client_gen import DPClientInvocationError, DPClientMethodCallContext

# isort: LOCAL
from stratis_cli._actions._utils import long_running_operation


class LongRunningOperationTestCase(unittest.TestCase):
    """
    Test long_running_operation error paths that don't show up in the sim
    engine.
    """

    def test_catch_dbus_exception(self):
        """
        Should succeed because it catches the distinguishing NoReply D-Bus
        error from the identified method.
        """

        def raises_error(_):
            raise DPClientInvocationError(
                "fake", "intf", DPClientMethodCallContext("MethodName", [])
            ) from dbus.exceptions.DBusException(
                name="org.freedesktop.DBus.Error.NoReply"
            )

        self.assertIsNone(
            long_running_operation(method_names=["MethodName"])(raises_error)(None)
        )

    def test_raise_dbus_exception_no_name_match(self):
        """
        Should succeed because it catches the distinguishing NoReply D-Bus
        error from the identified method.
        """

        def raises_error(_):
            raise DPClientInvocationError(
                "fake", "intf", DPClientMethodCallContext("MethodName", [])
            ) from dbus.exceptions.DBusException(
                name="org.freedesktop.DBus.Error.NoReply"
            )

        with self.assertRaises(DPClientInvocationError):
            long_running_operation(method_names=["OtherMethodName"])(raises_error)(None)

    def test_no_dbus_exception(self):
        """
        Should raise an exception that was previously raised.
        """

        def raises_error(_):
            raise DPClientInvocationError("fake", "intf", None)

        with self.assertRaises(DPClientInvocationError):
            long_running_operation(method_names=["OtherMethodName"])(raises_error)(None)
