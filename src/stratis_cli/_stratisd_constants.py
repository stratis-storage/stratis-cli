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

from ._error_codes import PoolMaintenanceErrorCode


class StratisdErrors(IntEnum):
    """
    Stratisd Errors
    """

    OK = 0
    ERROR = 1

    @staticmethod
    def from_int(code):
        """
        From an integer code, return the value.

        :param int code: the code
        :rtype: StratisdErrors
        :raises: StopIteration
        """
        return next(item for item in StratisdErrors if code == int(item))

    def __str__(self):
        if self is StratisdErrors.OK:
            return "OK"
        if self is StratisdErrors.ERROR:
            return "ERROR"
        assert False, "impossible value reached"  # pragma: no cover


class BlockDevTiers(IntEnum):
    """
    Tier to which a blockdev device belongs.
    """

    DATA = 0
    CACHE = 1

    @staticmethod
    def from_int(code):
        """
        From an integer code, return the value.

        :param int code: the code
        :rtype: StratisdErrors
        :raises: StopIteration
        """
        return next(item for item in BlockDevTiers if code == int(item))

    def __str__(self):
        if self is BlockDevTiers.DATA:
            return "DATA"
        if self is BlockDevTiers.CACHE:
            return "CACHE"
        assert False, "impossible value reached"  # pragma: no cover


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
    MANAGED_OBJECTS = "managed_objects_report"
    STOPPED_POOLS = "stopped_pools"

    def __str__(self):
        return self.value


class PoolActionAvailability(IntEnum):
    """
    What category of interactions a pool is enabled for.
    """

    FULLY_OPERATIONAL = 0
    NO_IPC_REQUESTS = 1
    NO_POOL_CHANGES = 2

    def __str__(self):
        if self is PoolActionAvailability.FULLY_OPERATIONAL:
            return "fully_operational"
        if self is PoolActionAvailability.NO_IPC_REQUESTS:
            return "no_ipc_requests"
        if self is PoolActionAvailability.NO_POOL_CHANGES:  # pragma: no cover
            return "no_pool_changes"

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

        return codes


class PoolIdType(Enum):
    """
    Whether the pool identifier is a UUID or a name.
    """

    UUID = "uuid"
    NAME = "name"

    def __str__(self):
        return self.value
