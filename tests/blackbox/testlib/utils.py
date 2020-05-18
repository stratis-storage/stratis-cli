# Copyright 2019 Red Hat, Inc.
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
Utility functions for blackbox testing.
"""
# isort: STDLIB
import base64
import os
import random
import string
from subprocess import PIPE, Popen
from tempfile import NamedTemporaryFile

# isort: THIRDPARTY
import dbus
import psutil

# Name prefix, so that we hopefully don't destroy any end user data by mistake!
TEST_PREF = os.getenv("STRATIS_UT_PREFIX", "STRATI$_DE$TROY_ME!_")


def p_n():
    """
    Return a random pool name
    :return: Random String
    """
    return TEST_PREF + "pool" + random_string()


def fs_n():
    """
    Return a random FS name
    :return: Random String
    """
    return TEST_PREF + "fs" + random_string()


def random_string(length=4):
    """
    Generates a random string
    :param length: Length of random string
    :return: String
    """
    return "{0}".format(
        "".join(random.choice(string.ascii_uppercase) for _ in range(length))
    )


def process_exists(name):
    """
    Look through processes, using their pids, to find one matching 'name'.
    Return None if no such process found, else return the pid.
    :param name: name of process to check
    :type name: str
    :return: pid or None
    :rtype: int or NoneType
    """
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.name() == name:
                return proc.pid
        except psutil.NoSuchProcess:
            pass

    return None


def umount_mdv():
    """
    Locate and umount any stratis mdv mounts
    :return: None
    """
    with open("/proc/self/mounts", "r") as mounts:
        for line in mounts.readlines():
            if "/stratis/.mdv-" in line:
                mountpoint = line.split()[1]
                exec_command(["umount", mountpoint])


def exec_command(cmd):
    """
    Executes the specified infrastructure command.

    :param cmd: command to execute
    :type cmd: list of str
    :returns: standard output
    :rtype: str
    :raises RuntimeError: if exit code is non-zero
    """
    exit_code, stdout_text, stderr_text = exec_test_command(cmd)

    if exit_code != 0:
        raise RuntimeError(
            "exec_command: non-zero exit code: %d\nSTDOUT=%s\nSTDERR=%s"
            % (exit_code, stdout_text, stderr_text)
        )
    return stdout_text


def exec_test_command(cmd):
    """
    Executes the specified test command
    :param cmd: Command and arguments as list
    :type cmd: list of str
    :returns: (exit code, std out text, std err text)
    :rtype: triple of int * str * str
    """
    process = Popen(cmd, stdout=PIPE, stderr=PIPE, close_fds=True, env=os.environ)
    result = process.communicate()
    return (
        process.returncode,
        bytes(result[0]).decode("utf-8"),
        bytes(result[1]).decode("utf-8"),
    )


class KernelKey:  # pylint: disable=attribute-defined-outside-init
    """
    A handle for operating on keys in the kernel keyring. The specified key will
    be available for the lifetime of the test when used with the Python with
    keyword and will be cleaned up at the end of the scope of the with block.
    """

    _OK = 0
    _BUS = dbus.SystemBus()
    _BUS_NAME = "org.storage.stratis2"
    _TOP_OBJECT = "/org/storage/stratis2"
    _MANAGER_IFACE = "org.storage.stratis2.Manager.r1"

    def __init__(self, key_data):
        """
        Initialize a key with the provided key data (passphrase).
        :param bytes key_data: The desired key contents
        """
        self._key_data = key_data

        self._top_object = self._BUS.get_object(self._BUS_NAME, self._TOP_OBJECT)
        self._manager_iface = dbus.Interface(self._top_object, self._MANAGER_IFACE)

    def __enter__(self):
        """
        This method allows KernelKey to be used with the "with" keyword.
        :return: The key description that can be used to access the
                 provided key data in __init__.
        :raises RuntimeError: if setting the key using the stratisd D-Bus API
                              returns a non-zero return code
        """
        with open("/dev/urandom", "rb") as urandom_f:
            self._key_desc = base64.b64encode(urandom_f.read(16)).decode("utf-8")

        with NamedTemporaryFile(mode="w") as temp_file:
            temp_file.write(self._key_data)
            temp_file.flush()

            with open(temp_file.name, "r") as fd_for_dbus:
                (_, return_code, message) = self._manager_iface.SetKey(
                    self._top_object,
                    {
                        "key_desc": self._key_desc,
                        "key_fd": fd_for_dbus.fileno(),
                        "interactive": False,
                    },
                )

        if return_code != self._OK:
            raise RuntimeError(
                "Setting the key using stratisd failed with an error: %s" % message
            )

        return self._key_desc

    def __exit__(self, exception_type, exception_value, traceback):
        message = None
        try:
            (_, return_code, message) = self._manager_iface.UnsetKey(
                self._top_object, {"key_desc": self._key_desc}
            )

            if return_code != self._OK:
                raise RuntimeError(
                    "Unsetting the key using stratisd failed with an error: %s"
                    % message
                )
        except Exception as rexc:
            if exception_value is None:
                raise rexc
            raise rexc from exception_value
