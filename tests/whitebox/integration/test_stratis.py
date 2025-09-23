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
Test 'stratisd'.
"""

# isort: STDLIB
from unittest.mock import patch

# isort: THIRDPARTY
import dbus

# isort: FIRSTPARTY
from dbus_python_client_gen import (
    DPClientGetPropertyContext,
    DPClientInvocationError,
    DPClientMethodCallContext,
)

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes, run
from stratis_cli._actions import MANAGER_0_INTERFACE
from stratis_cli._errors import StratisCliStratisdVersionError

from ._misc import RUNNER, TEST_RUNNER, RunTestCase, SimTestCase

_ERROR = StratisCliErrorCodes.ERROR


class StratisTestCase(SimTestCase):
    """
    Test meta information about stratisd.
    """

    _MENU = ["--propagate", "daemon"]

    def test_stratis_version(self):
        """
        Getting version should just succeed.
        """
        command_line = self._MENU + ["version"]
        TEST_RUNNER(command_line)


class PropagateTestCase(RunTestCase):
    """
    Verify correct operation of --propagate flag.
    """

    def test_propagate(self):
        """
        If propagate is set, the expected exception will propagate.
        """
        command_line = ["--propagate", "daemon", "version"]
        self.check_error(dbus.exceptions.DBusException, command_line, _ERROR)

    def test_not_propagate(self):
        """
        If propagate is not set, the exception will be SystemExit.
        """
        command_line = ["daemon", "version"]
        with self.assertRaises(SystemExit):
            RUNNER(command_line)


class StratisdVersionTestCase(SimTestCase):
    """
    Test behavior of stratis on incompatible versions of stratisd.
    """

    def test_outdated_stratisd_version(self):
        """
        Verify that an outdated version of stratisd will produce a
        StratisCliStratisdVersionError.
        """
        # pylint: disable=import-outside-toplevel
        # isort: LOCAL
        from stratis_cli._actions import _data

        command_line = ["--propagate", "daemon", "version"]

        # pylint: disable=protected-access
        with patch.object(
            _data.Manager0.Properties.Version,
            "Get",
            return_value="1.0.0",
        ):
            self.check_error(StratisCliStratisdVersionError, command_line, _ERROR)


class TestTimeoutErrorResponse(SimTestCase):
    """
    Test stratisd error response when timing out on different methods.
    """

    def test_stratisd_version_not_return(self):
        """
        Verify behavior of stratisd Version not obtained in reasonable time.
        Fake the correct D-Bus exception.
        """
        # pylint: disable=import-outside-toplevel
        # isort: LOCAL
        from stratis_cli._actions import _data

        command_line = ["--propagate", "key", "list"]

        class _VersionGetter:  # pylint: disable=too-few-public-methods
            @staticmethod
            def Get(_):  # pylint: disable=invalid-name, no-method-argument
                """
                Mock Get method.
                """
                dbus_exception = dbus.exceptions.DBusException("msg")
                dbus_exception._dbus_error_name = "org.freedesktop.DBus.Error.NoReply"  # pylint: disable=protected-access
                raise DPClientInvocationError(
                    "fake timeout error",
                    MANAGER_0_INTERFACE,
                    DPClientGetPropertyContext("Version"),
                ) from dbus_exception

        # pylint: disable=protected-access
        with patch.object(
            _data.Manager0.Properties.Version,
            "Get",
            _VersionGetter.Get,
        ):
            self.check_error(DPClientInvocationError, command_line, _ERROR)

    def test_dbus_action_method_not_return(self):
        """
        Verify behavior of stratisd ListKeys method result not obtained in
        reasonable time. Fake the correct D-Bus exception.
        """
        # pylint: disable=import-outside-toplevel
        command_line = ["--propagate", "key", "list"]

        # isort: LOCAL
        from stratis_cli._actions import _data

        class _KeyLister:  # pylint: disable=too-few-public-methods
            @staticmethod
            def ListKeys(
                _object, _args
            ):  # pylint: disable=invalid-name, no-method-argument
                """
                Mock ListKeys method.
                """
                dbus_exception = dbus.exceptions.DBusException("msg")
                dbus_exception._dbus_error_name = "org.freedesktop.DBus.Error.NoReply"  # pylint: disable=protected-access
                raise DPClientInvocationError(
                    "fake timeout error",
                    "intf",
                    DPClientMethodCallContext("ListKeys", []),
                ) from dbus_exception

        # pylint: disable=protected-access
        with patch.object(_data.Manager.Methods, "ListKeys", _KeyLister.ListKeys):
            self.check_error(DPClientInvocationError, command_line, _ERROR)


class KeyboardInterruptTestCase(SimTestCase):
    """
    Test behavior of stratis on KeyboardInterrupt.
    """

    def test_catch_keyboard_exception(self):
        """
        Verify that the KeyboardInterrupt is propagated by the run() method.
        ./bin/stratis contains a try block at the outermost level which
        then catches the KeyboardInterrupt and exits with an error message.
        The KeyboardInterrupt is most likely raised in the dbus-python
        method which is actually communicating on the D-Bus, but it is
        fairly difficult to get at that method. Instead settle for getting
        at the calling method generated by dbus-python-client-gen.
        """

        # pylint: disable=import-outside-toplevel
        # isort: LOCAL
        from stratis_cli._actions import _data

        with patch.object(
            _data.Manager0.Properties.Version, "Get", side_effect=KeyboardInterrupt()
        ):
            with self.assertRaises(KeyboardInterrupt):
                run()(["daemon", "version"])
