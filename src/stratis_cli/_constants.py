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


class PoolIdType(Enum):
    """
    Whether the pool identifier is a UUID or a name.
    """

    UUID = 0
    NAME = 1


class EncryptionMethod(Enum):
    """
    Encryption method.
    """

    KEYRING = "keyring"
    CLEVIS = "clevis"

    def __str__(self):
        return self.value


class Clevis(Enum):
    """
    Clevis encryption methods.
    """

    NBDE = "nbde"
    TANG = "tang"
    TPM2 = "tpm2"

    def __str__(self):
        return self.value
