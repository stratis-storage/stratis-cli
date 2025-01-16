# Copyright 2021 Red Hat, Inc.
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
General constants.
"""
# isort: STDLIB
from enum import Enum


class YesOrNo(Enum):
    """
    Generic Yes or No enum, for toggling modes in CI.
    """

    YES = "yes"
    NO = "no"

    def __bool__(self):
        return self is YesOrNo.YES

    def __str__(self):
        return self.value


class IdType(Enum):
    """
    Whether the pool identifier is a UUID or a name.
    """

    UUID = 0
    NAME = 1


class Id:
    """
    Generic management of ids when either a UUID or name can be used.
    """

    def __init__(self, id_type, id_value):
        """
        Initialize the object.
        """
        self.id_type = id_type
        self.id_value = id_value

    def managed_objects_key(self):
        """
        Return key for managed objects.

        Precondition: the D-Bus property that identifies the Name or the
        Uuid will always be the same.
        """
        return {"Uuid" if self.id_type is IdType.UUID else "Name": self.dbus_value()}

    def is_uuid(self):
        """
        True if the id is a UUID, otherwise false.
        """
        return self.id_type == IdType.UUID

    def dbus_value(self):
        """
        Returns a string value for matching D-Bus things.
        """
        return self.id_value.hex if self.id_type is IdType.UUID else self.id_value

    def __str__(self):
        pool_id_type_str = "UUID" if self.id_type is IdType.UUID else "name"
        return f"{pool_id_type_str} {self.id_value}"


class EncryptionMethod(Enum):
    """
    Encryption method.
    """

    KEYRING = "keyring"
    CLEVIS = "clevis"

    def __str__(self):
        return self.value


class UnlockMethod(Enum):
    """
    Unlock method.
    """

    ANY = "any"
    CLEVIS = "clevis"
    KEYRING = "keyring"

    def __str__(self):
        return self.value

    def legacy_token_slot(self):  # pragma: no cover
        """
        Token slot for legacy pool.
        """
        assert self in (UnlockMethod.KEYRING, UnlockMethod.CLEVIS)
        if self is UnlockMethod.KEYRING:
            return 1
        return 2


class Clevis(Enum):
    """
    Clevis encryption methods.
    """

    NBDE = "nbde"
    TANG = "tang"
    TPM2 = "tpm2"

    def __str__(self):
        return self.value


class IntegrityTagSpec(Enum):
    """
    Options for specifying integrity tag size.
    """

    B0 = "0b"
    B32 = "32b"
    B512 = "512b"

    def __str__(self):
        return self.value


class IntegrityOption(Enum):
    """
    Options for specifying integrity choices on create.
    """

    NO = "no"
    PRE_ALLOCATE = "pre-allocate"

    def __str__(self):
        return self.value
