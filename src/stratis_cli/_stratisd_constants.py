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
from typing import Any, List, Mapping

from ._error_codes import PoolMaintenanceErrorCode


class StratisdErrors(IntEnum):
    """
    Stratisd Errors
    """

    OK = 0
    ERROR = 1

    def __str__(self):
        return self.name


class BlockDevTiers(IntEnum):
    """
    Tier to which a blockdev device belongs.
    """

    DATA = 0
    CACHE = 1

    def __str__(self):
        return self.name


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

    fully_operational = 0  # pylint: disable=invalid-name
    no_ipc_requests = 1  # pylint: disable=invalid-name
    no_pool_changes = 2  # pylint: disable=invalid-name

    def pool_maintenance_error_codes(self) -> List[PoolMaintenanceErrorCode]:
        """
        Return the list of PoolMaintenanceErrorCodes for this availability.

        :rtype: list of PoolMaintenanceErrorCode
        """
        codes = []
        if self >= PoolActionAvailability.no_ipc_requests:
            codes.append(PoolMaintenanceErrorCode.NO_IPC_REQUESTS)

        if self >= PoolActionAvailability.no_pool_changes:
            codes.append(PoolMaintenanceErrorCode.NO_POOL_CHANGES)

        return codes


class MetadataVersion(Enum):
    """
    Stratis metadata version.
    """

    V1 = 1
    V2 = 2

    def __str__(self):
        return str(self.value)


class ClevisInfo:
    """
    Store a representation of Clevis encryption info
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, pin: str, config: Mapping[str, Any]):
        """
        Initialize clevis information.

        :param str pin: the Clevis "pin"
        :param dict config: the JSON config corresponding to the pin
        """
        self.pin = pin
        self.config = config
