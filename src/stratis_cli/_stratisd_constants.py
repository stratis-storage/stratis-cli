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
Stratisd error classes.
"""

# isort: STDLIB
from enum import Enum, IntEnum


def value_to_name(klass):
    """
    Generate a function to convert an IntEnum value to its name.

    :param type klass: the class defining the IntEnum
    :returns: a function to convert a single number to a name
    :rtype: int -> str
    """

    def the_func(num, terse_unknown=False):
        """
        Convert the enum value to a string which is just its name.
        Replace underscores in the name with spaces.

        If there is no name for the value, return a special string.

        :param int num: the number to convert
        :param bool terse_unknown: terse format for unknown name, default false
        :returns: the name for the number or an error string
        :rtype: str
        """
        try:
            the_str = str(klass(num)).rsplit(".")[-1].replace("_", " ")

        # This branch is taken only if the constants defined here do not
        # match those defined in stratisd. We should remedy such a situation
        # very rapidly.
        except ValueError:  # pragma: no cover
            the_str = (
                "???"
                if terse_unknown
                else "Unknown value (%s) for %s constant" % (num, klass.__name__)
            )
        return the_str

    return the_func


class StratisdErrors(IntEnum):
    """
    Stratisd Errors
    """

    OK = 0
    ERROR = 1

    ALREADY_EXISTS = 2
    BUSY = 3
    INTERNAL_ERROR = 4
    NOT_FOUND = 5


STRATISD_ERROR_TO_NAME = value_to_name(StratisdErrors)


class RedundancyCodes(IntEnum):
    """
    Redundancy Codes
    """

    NONE = 0


REDUNDANCY_CODE_TO_NAME = value_to_name(RedundancyCodes)


class BlockDevTiers(IntEnum):
    """
    Tier to which a blockdev device belongs.
    """

    Data = 0
    Cache = 1


BLOCK_DEV_TIER_TO_NAME = value_to_name(BlockDevTiers)


class EncryptionMethod(Enum):
    """
    Encryption method, used as argument to unlock.
    """

    KEYRING = "keyring"
    CLEVIS = "clevis"

    def __str__(self):
        return self.value


CLEVIS_KEY_TANG_TRUST_URL = "stratis:tang:trust_url"
CLEVIS_PIN_TANG = "tang"
CLEVIS_PIN_TPM2 = "tpm2"
CLEVIS_KEY_THP = "thp"
CLEVIS_KEY_URL = "url"
