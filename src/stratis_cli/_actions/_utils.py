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
import json
from uuid import UUID

from .._constants import IdType
from .._stratisd_constants import (
    CLEVIS_KEY_TANG_TRUST_URL,
    CLEVIS_KEY_THP,
    CLEVIS_KEY_URL,
    CLEVIS_PIN_TANG,
    CLEVIS_PIN_TPM2,
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
    def get_info_from_namespace(namespace):
        """
        Get clevis info, if any, from the namespace.

        :param namespace: namespace set up by the parser

        :returns: clevis info or None
        :rtype: ClevisInfo or NoneType
        """
        clevis_info = None
        if namespace.clevis is not None:
            if namespace.clevis in ("nbde", "tang"):
                assert namespace.tang_url is not None

                assert namespace.trust_url or namespace.thumbprint is not None

                clevis_config = {CLEVIS_KEY_URL: namespace.tang_url}
                if namespace.trust_url:
                    clevis_config[CLEVIS_KEY_TANG_TRUST_URL] = True
                else:
                    assert namespace.thumbprint is not None
                    clevis_config[CLEVIS_KEY_THP] = namespace.thumbprint

                clevis_info = ClevisInfo(CLEVIS_PIN_TANG, clevis_config)

            elif namespace.clevis == "tpm2":
                clevis_info = ClevisInfo(CLEVIS_PIN_TPM2, {})

            else:
                raise AssertionError(
                    f"unexpected value {namespace.clevis} for clevis option"
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

    def consistent(self):
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
                (pin, config) = value
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


class PoolSelector:
    """
    Methods to help locate a pool by one of its identifiers.
    """

    def __init__(self, pool_id_type, value):
        """
        Initializer.

        :param IdType pool_id_type: the id type
        :param object value: the value, determined by the type
        """
        self.pool_id_type = pool_id_type
        self.value = value

    def managed_objects_key(self):
        """
        Get the key for searching GetManagedObjects result.
        :rtype: dict of str * object
        :returns: a dict containing a correct configuration for pools() method
        """
        return (
            {"Uuid": self.value.hex}
            if self.pool_id_type is IdType.UUID
            else {"Name": self.value}
        )

    def stopped_pools_func(self):
        """
        Get a function appropriate for searching StoppedPools D-Bus property.
        :returns: a function for selecting from StoppedPools items
        :rtype: (str * (dict of (str * object))) -> bool
        """
        if self.pool_id_type is IdType.UUID:
            selection_value = self.value.hex

            def selection_func(uuid, _info):
                return uuid == selection_value

        else:
            selection_value = self.value

            def selection_func(_uuid, info):
                return info.get("name") == selection_value

        return selection_func

    def __str__(self):
        pool_id_type_str = "UUID" if self.pool_id_type is IdType.UUID else "name"
        return f"pool with {pool_id_type_str} {self.value}"
