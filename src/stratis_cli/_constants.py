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
from abc import ABC, abstractmethod
from argparse import Namespace
from enum import Enum
from typing import Callable, Dict, Union
from uuid import UUID


class YesOrNo(Enum):
    """
    Generic Yes or No enum, for toggling modes in CI.
    """

    YES = "yes"
    NO = "no"

    def __bool__(self) -> bool:
        return self is YesOrNo.YES

    def __str__(self) -> str:
        return self.value


class IdType(Enum):
    """
    Whether the pool identifier is a UUID or a name.
    """

    UUID = "UUID"
    NAME = "name"

    def __str__(self) -> str:
        return self.value


class Id(ABC):
    """
    Generic management of ids when either a UUID or name can be used.
    """

    def __init__(self, id_type: IdType, id_value: Union[UUID, str]):
        """
        Initialize the object.
        """
        assert (id_type is IdType.UUID) == isinstance(id_value, UUID)

        self.id_type = id_type
        self.id_value = id_value

    def managed_objects_key(
        self,
    ):
        """
        Return key for managed objects.

        Precondition: the D-Bus property that identifies the Name or the
        Uuid will always be the same.
        """
        return (
            {"Uuid": self.id_value.hex}  # pyright: ignore [ reportAttributeAccessIssue]
            if self.id_type is IdType.UUID
            else {"Name": self.id_value}
        )

    def dbus_args(self):
        """
        Specify an id, id_type D-Bus argument.
        """
        return (
            {"id": self.id_value, "id_type": "name"}
            if self.id_type is IdType.NAME
            else {
                "id": self.id_value.hex,  # pyright: ignore [ reportAttributeAccessIssue]
                "id_type": "uuid",
            }
        )

    @abstractmethod
    def __str__(self) -> str:
        """
        The usual __str__ method
        """

    @staticmethod
    @abstractmethod
    def from_parser_namespace(namespace, *, required=True):
        """
        Make an Id from a parser namespace.
        :param bool required: True if --uuid/--name pair required by parser
        """


class PoolId(Id):
    """
    Pool id.
    """

    def __str__(self) -> str:
        return f"pool with {self.id_type} {self.id_value}"

    @staticmethod
    def from_parser_namespace(  # pyright: ignore [reportIncompatibleMethodOverride]
        namespace: Namespace, *, required=True
    ):
        assert hasattr(namespace, "name") and hasattr(namespace, "uuid")
        if namespace.uuid is not None:
            return PoolId(IdType.UUID, namespace.uuid)
        if namespace.name is not None:
            return PoolId(IdType.NAME, namespace.name)

        assert not required

        return None

    def stopped_pools_func(self) -> Callable[[str, Dict], bool]:
        """
        Function for selecting a pool from stopped pools.
        """
        selection_value = (
            self.id_value.hex  # pyright: ignore [reportAttributeAccessIssue]
            if self.id_type is IdType.UUID
            else self.id_value
        )

        return (
            (lambda uuid, info: uuid == selection_value)
            if self.id_type is IdType.UUID
            else (lambda uuid, info: info.get("name") == selection_value)
        )


class FilesystemId(Id):
    """
    Filesystem id.
    """

    def __str__(self) -> str:
        return f"filesystem with {self.id_type} {self.id_value}"

    @staticmethod
    def from_parser_namespace(  # pyright: ignore [reportIncompatibleMethodOverride]
        namespace: Namespace, *, required=True
    ):
        assert hasattr(namespace, "name") and hasattr(namespace, "uuid")
        if namespace.uuid is not None:
            return FilesystemId(IdType.UUID, namespace.uuid)
        if namespace.name is not None:
            return FilesystemId(IdType.NAME, namespace.name)

        assert not required

        return None


class EncryptionMethod(Enum):
    """
    Encryption method.
    """

    KEYRING = "keyring"
    CLEVIS = "clevis"

    def __str__(self) -> str:
        return self.value


class UnlockMethod(Enum):
    """
    Unlock method.
    """

    ANY = "any"
    CLEVIS = "clevis"
    KEYRING = "keyring"

    def __str__(self) -> str:
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

    def __str__(self) -> str:
        return self.value


class IntegrityTagSpec(Enum):
    """
    Options for specifying integrity tag size.
    """

    B0 = "0b"
    B32 = "32b"
    B512 = "512b"

    def __str__(self) -> str:
        return self.value


class IntegrityOption(Enum):
    """
    Options for specifying integrity choices on create.
    """

    NO = "no"
    PRE_ALLOCATE = "pre-allocate"

    def __str__(self) -> str:
        return self.value
