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
Methods and classes that do infrastructure tasks.
"""
# isort: STDLIB
import base64
from tempfile import NamedTemporaryFile

from .dbus import StratisDbus
from .utils import exec_command


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


def clean_up():
    """
    Try to clean up after a test failure.

    :return: None
    """

    exec_command(["udevadm"], ["settle"])

    umount_mdv()

    error_strings = []

    def check_result(result, format_str, format_str_args):
        if result is None:
            return
        (_, code, msg) = result
        if code == 0:
            return
        error_strings.append("%s: %s" % ((format_str % format_str_args), msg))

    # Remove FS
    for name, pool_name in StratisDbus.fs_list().items():
        check_result(
            StratisDbus.fs_destroy(pool_name, name),
            "failed to destroy filesystem %s in pool %s",
            (name, pool_name),
        )

    # Remove Pools
    for name in StratisDbus.pool_list():
        check_result(StratisDbus.pool_destroy(name), "failed to destroy pool %s", name)

    # Unset all Stratis keys
    for key in StratisDbus.get_keys():
        check_result(StratisDbus.unset_key(key), "failed to unset key %s", key)

    # Report an error if any filesystems, pools or keys are found to be
    # still in residence
    remnant_filesystems = StratisDbus.fs_list()
    if remnant_filesystems != {}:
        error_strings.append(
            "remnant filesystems: %s"
            % ", ".join(
                map(
                    lambda x: "%s in pool %s" % (x[0], x[1]),
                    remnant_filesystems.items(),
                )
            )
        )

    remnant_pools = StratisDbus.pool_list()
    if remnant_pools != []:
        error_strings.append("remnant pools: %s" % ", ".join(remnant_pools))

    remnant_keys = StratisDbus.get_keys()
    if remnant_keys != []:
        error_strings.append("remnant keys: %s" % ", ".join(remnant_keys))

    if error_strings != []:
        raise RuntimeError("clean_up failed: %s" % "; ".join(error_strings))


class KernelKey:  # pylint: disable=attribute-defined-outside-init
    """
    A handle for operating on keys in the kernel keyring. The specified key will
    be available for the lifetime of the test when used with the Python with
    keyword and will be cleaned up at the end of the scope of the with block.
    """

    _OK = 0

    def __init__(self, key_data):
        """
        Initialize a key with the provided key data (passphrase).
        :param bytes key_data: The desired key contents
        """
        self._key_data = key_data

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

            (_, return_code, message) = StratisDbus.set_key(self._key_desc, temp_file)

        if return_code != KernelKey._OK:
            raise RuntimeError(
                "Setting the key using stratisd failed with an error: %s" % message
            )

        return self._key_desc

    def __exit__(self, exception_type, exception_value, traceback):
        message = None
        try:
            (_, return_code, message) = StratisDbus.unset_key(self._key_desc)

            if return_code != KernelKey._OK:
                raise RuntimeError(
                    "Unsetting the key using stratisd failed with an error: %s"
                    % message
                )
        except Exception as rexc:
            if exception_value is None:
                raise rexc
            raise rexc from exception_value
