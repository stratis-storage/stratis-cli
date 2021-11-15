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

from ._constants import PoolMaintenanceErrorCode


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
            the_str = str(klass(num)).rsplit(".", maxsplit=1)[-1].replace("_", " ")

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

    DATA = 0
    CACHE = 1


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


class ReportKey(Enum):
    """
    Report identifiers.

    Note: "managed_objects_report" is not a key recognized by stratisd.
    However, since the other constants are, and they are all used together,
    this type is defined with the other stratisd constants.
    """

    ENGINE_STATE = "engine_state_report"
    ERRORED_POOL = "errored_pool_report"
    MANAGED_OBJECTS = "managed_objects_report"

    def __str__(self):
        return self.value


class PoolActionAvailability(IntEnum):
    """
    What category of interactions a pool is enabled for.
    """

    FULLY_OPERATIONAL = 0
    NO_IPC_REQUESTS = 1
    NO_POOL_CHANGES = 2
    NO_WRITE_IO = 3

    def __str__(self):
        if self is PoolActionAvailability.FULLY_OPERATIONAL:
            return "fully_operational"
        if self is PoolActionAvailability.NO_IPC_REQUESTS:
            return "no_ipc_requests"
        if self is PoolActionAvailability.NO_POOL_CHANGES:
            return "no_pool_changes"
        if self is PoolActionAvailability.NO_WRITE_IO:  # pragma: no cover
            return "no_write_io"

        assert False, "impossible value reached"  # pragma: no cover

    @staticmethod
    def from_str(code_str):
        """
        Get ActionAvailability object from a string.
        :param str code_str: a code string
        :rtype: str or NoneType
        """
        for item in list(PoolActionAvailability):
            if code_str == str(item):
                return item
        return None

    def pool_maintenance_error_codes(self):
        """
        Return the list of PoolMaintenanceErrorCodes for this availability.

        :rtype: list of PoolMaintenanceErrorCode
        """
        codes = []
        if self >= PoolActionAvailability.NO_IPC_REQUESTS:
            codes.append(PoolMaintenanceErrorCode.NO_IPC_REQUESTS)

        if self >= PoolActionAvailability.NO_POOL_CHANGES:
            codes.append(PoolMaintenanceErrorCode.NO_POOL_CHANGES)

        if self >= PoolActionAvailability.NO_WRITE_IO:
            codes.append(PoolMaintenanceErrorCode.READ_ONLY)

        return codes
