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

from .._constants import Clevis
from .._errors import (
    StratisCliKeyfileNotFoundError,
    StratisCliPassphraseEmptyError,
    StratisCliPassphraseMismatchError,
)
from .._stratisd_constants import (
    CLEVIS_KEY_TANG_TRUST_URL,
    CLEVIS_KEY_THP,
    CLEVIS_KEY_URL,
    CLEVIS_PIN_TANG,
    CLEVIS_PIN_TPM2,
    MetadataVersion,
)


class ClevisInfo:
    """
    Store a representation of Clevis encryption info
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, pin, config):
        """
        Initialize clevis information.

        :param str pin: the Clevis "pin"
        :param dict config: the JSON config corresponding to the pin
        """
        self.pin = pin
        self.config = config

    @staticmethod
    def get_info(options):
        """
        Get clevis info from the clevis options.

        :param options: ClevisEncryptionOptions

        :returns: clevis info or None
        :rtype: ClevisInfo or NoneType
        """
        if options.clevis in (Clevis.NBDE, Clevis.TANG):
            assert options.tang_url is not None

            assert options.trust_url or options.thumbprint is not None

            clevis_config = {CLEVIS_KEY_URL: options.tang_url}
            if options.trust_url:
                clevis_config[CLEVIS_KEY_TANG_TRUST_URL] = True
            else:
                assert options.thumbprint is not None
                clevis_config[CLEVIS_KEY_THP] = options.thumbprint

            clevis_info = ClevisInfo(CLEVIS_PIN_TANG, clevis_config)

        elif options.clevis is Clevis.TPM2:
            clevis_info = ClevisInfo(CLEVIS_PIN_TPM2, {})

        else:
            raise AssertionError(
                f"unexpected value {options.clevis} for clevis option"
            )  # pragma: no cover

        return clevis_info


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

    def __str__(self):  # pragma: no cover
        return self.value


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


class PoolSelector:
    """
    Methods to help locate a pool by one of its identifiers.
    """

    def __init__(self, pool_id):
        """
        Initializer.

        :param Id pool_id: the id
        """
        self.pool_id = pool_id

    def managed_objects_key(self):
        """
        Get the key for searching GetManagedObjects result.
        :rtype: dict of str * object
        :returns: a dict containing a correct configuration for pools() method
        """
        return self.pool_id.managed_objects_key()

    def stopped_pools_func(self):
        """
        Get a function appropriate for searching StoppedPools D-Bus property.
        :returns: a function for selecting from StoppedPools items
        :rtype: (str * (dict of (str * object))) -> bool
        """
        selection_value = self.pool_id.dbus_value()

        return (
            (lambda uuid, info: uuid == selection_value)
            if self.pool_id.is_uuid()
            else (lambda uuid, info: info.get("name") == selection_value)
        )

    def __str__(self):
        return f"pool with {self.pool_id}"


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
