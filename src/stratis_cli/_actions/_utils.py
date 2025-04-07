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
Miscellaneous functions.
"""

# isort: STDLIB
import errno
import json
import os
import sys
import termios
from enum import Enum
from uuid import UUID

from .._errors import (
    StratisCliKeyfileNotFoundError,
    StratisCliPassphraseEmptyError,
    StratisCliPassphraseMismatchError,
)
from .._stratisd_constants import ClevisInfo, MetadataVersion

_STRICT_POOL_FEATURES = bool(int(os.environ.get("STRATIS_STRICT_POOL_FEATURES", False)))


class EncryptionInfo:  # pylint: disable=too-few-public-methods
    """
    Generic information about a single encryption method.
    """

    def __init__(self, info):
        """
        Initializer.
        :param info: info about an encryption method, as a dbus-python type
        """
        (consistent, info) = info
        if consistent:
            (encrypted, value) = info
            self.value = value if encrypted else None
        else:
            # No tests that generate inconsistent encryption information
            self.error = str(info)  # pragma: no cover

    # This method is only invoked when displaying legacy pool information
    def consistent(self):  # pragma: no cover
        """
        True if consistent, otherwise False.
        """
        return not hasattr(self, "error")


class EncryptionInfoClevis(EncryptionInfo):  # pylint: disable=too-few-public-methods
    """
    Encryption info for Clevis
    """

    def __init__(self, info):
        super().__init__(info)

        # We don't test with Clevis for coverage
        if hasattr(self, "value"):  # pragma: no cover
            value = self.value
            if value is not None:
                (pin, config) = value  # pyright: ignore [ reportGeneralTypeIssues ]
                self.value = ClevisInfo(str(pin), json.loads(str(config)))


class EncryptionInfoKeyDescription(
    EncryptionInfo
):  # pylint: disable=too-few-public-methods
    """
    Encryption info for kernel keyring
    """

    def __init__(self, info):
        super().__init__(info)

        # Our listing code excludes creating an object of this class without
        # it being consistent and set.
        if hasattr(self, "value"):  # pragma: no cover
            value = self.value
            if value is not None:
                self.value = str(value)


class Device:  # pylint: disable=too-few-public-methods
    """
    A representation of a device in a stopped pool.
    """

    def __init__(self, mapping):
        self.uuid = UUID(mapping["uuid"])
        self.devnode = str(mapping["devnode"])


class PoolFeature(Enum):
    """
    Elements of a pool feature set that may be exposed in the StoppedPools
    property.
    """

    ENCRYPTION = "encryption"
    INTEGRITY = "integrity"
    RAID = "raid"
    KEY_DESCRIPTION_PRESENT = "key_description_present"
    CLEVIS_PRESENT = "clevis_present"

    UNRECOGNIZED = None

    def __str__(self):
        if self is PoolFeature.UNRECOGNIZED:
            return "<UNRECOGNIZED>"
        return self.value

    @classmethod
    def _missing_(cls, value):
        if _STRICT_POOL_FEATURES:  # pragma: no cover
            return None
        return PoolFeature.UNRECOGNIZED  # pragma: no cover


class StoppedPool:  # pylint: disable=too-few-public-methods
    """
    A representation of a single stopped pool.
    """

    def __init__(self, pool_info):
        """
        Initializer.
        :param pool_info: a D-Bus structure
        """

        self.devs = [Device(info) for info in pool_info["devs"]]

        clevis_info = pool_info.get("clevis_info")
        self.clevis_info = (
            None if clevis_info is None else EncryptionInfoClevis(clevis_info)
        )

        key_description = pool_info.get("key_description")
        self.key_description = (
            None
            if key_description is None
            else EncryptionInfoKeyDescription(key_description)
        )

        name = pool_info.get("name")
        self.name = None if name is None else str(name)

        metadata_version_valid, metadata_version = pool_info["metadata_version"]
        try:
            self.metadata_version = (
                MetadataVersion(int(metadata_version))
                if metadata_version_valid
                else None
            )
        except ValueError:  # pragma: no cover
            self.metadata_version = None

        features_valid, features = pool_info["features"]
        self.features = (
            frozenset(PoolFeature(f) for f in features) if features_valid else None
        )


def get_pass(prompt):
    """
    Prompt for a passphrase on stdin.

    :param str prompt: prompt to display to user when fetching passphrase
    :return: password
    :rtype: str or None
    """
    print(prompt, end="")
    sys.stdout.flush()
    old_attrs = None
    try:  # pragma: no cover
        old_attrs = termios.tcgetattr(sys.stdin)
        new_attrs = termios.tcgetattr(sys.stdin)
        new_attrs[3] &= ~termios.ECHO
        new_attrs[3] |= termios.ECHONL
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, new_attrs)
    except termios.error as err:  # pragma: no cover
        if err.args[0] == errno.ENOTTY:
            print(
                "Warning: this device is not a TTY so the password may be echoed",
                file=sys.stderr,
            )
    except Exception:  # nosec pylint: disable=broad-exception-caught
        pass

    password = None
    try:
        password = sys.stdin.readline()
    except Exception as err:  # pragma: no cover
        if old_attrs is not None:
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, old_attrs)
        raise err

    if old_attrs is not None:
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, old_attrs)  # pragma: no cover
    return password.rstrip("\n")


def get_passphrase_fd(*, keyfile_path=None, verify=True):
    """
    Get a passphrase either from stdin or from a file.

    :param str keyfile_path: path to a keyfile, may be None
    :param bool verify: If verify is True, check password match

    :return: a file descriptor to pass on the D-Bus, what to close when done
    """
    if keyfile_path is None:
        password = get_pass("Enter passphrase followed by the return key: ")
        password_2 = get_pass("Verify passphrase entered: ") if verify else password

        if password != password_2:
            raise StratisCliPassphraseMismatchError()

        if len(password) == 0:
            raise StratisCliPassphraseEmptyError()

        (read, write) = os.pipe()
        os.write(write, password.encode("utf-8"))

        file_desc = read
        fd_to_close = write
    else:
        try:
            file_desc = os.open(keyfile_path, os.O_RDONLY)
            fd_to_close = file_desc
        except FileNotFoundError as err:
            raise StratisCliKeyfileNotFoundError(keyfile_path) from err

    return (file_desc, fd_to_close)


def fetch_stopped_pools_property(proxy):
    """
    Fetch the StoppedPools property from stratisd.
    :param proxy: proxy to the top object in stratisd
    :return: a representation of stopped devices
    :rtype: dict
    :raises StratisCliEngineError:
    """

    # pylint: disable=import-outside-toplevel
    from ._data import Manager

    return Manager.Properties.StoppedPools.Get(proxy)
