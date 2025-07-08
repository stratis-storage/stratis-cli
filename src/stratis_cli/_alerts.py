# Copyright 2022 Red Hat, Inc.
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
Error codes
"""
# isort: STDLIB
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Union


class Level(Enum):
    """
    Error levels.
    """

    ERROR = "E"
    WARNING = "W"
    INFO = "I"

    def __str__(self) -> str:
        return self.value


class PoolMaintenanceAlert(IntEnum):
    """
    Maintenance alerts for the pool.
    """

    NO_IPC_REQUESTS = 1
    NO_POOL_CHANGES = 2

    def __str__(self) -> str:
        return f"{Level.ERROR}M{str(self.value).zfill(3)}"

    def explain(self) -> str:
        """
        Return an explanation of the alert code.
        """
        if self is PoolMaintenanceAlert.NO_IPC_REQUESTS:
            return (
                "The pool will return an error on any IPC request that could "
                "cause a change in the pool state, for example, a request to "
                "rename a filesystem. It will still be able to respond to "
                "purely informational requests."
            )

        if self is PoolMaintenanceAlert.NO_POOL_CHANGES:
            return (
                "The pool is unable to manage itself by reacting to events, "
                "such as devicemapper events, that might require it to take "
                "any maintenance operations."
            )

        assert False, "impossible code reached"  # pragma: no cover

    def summarize(self) -> str:
        """
        Return a short summary of the alert.
        """
        if self is PoolMaintenanceAlert.NO_IPC_REQUESTS:
            return "Pool state changes not possible"

        if self is PoolMaintenanceAlert.NO_POOL_CHANGES:
            return "Pool maintenance operations not possible"

        assert False, "impossible code reached"  # pragma: no cover


class PoolAllocSpaceAlert(IntEnum):
    """
    Code if the pool has run out of space to allocate.
    """

    NO_ALLOC_SPACE = 1

    def __str__(self) -> str:
        return f"{Level.WARNING}S{str(self.value).zfill(3)}"

    def explain(self) -> str:
        """
        Return an explanation of the alert.
        """
        if self is PoolAllocSpaceAlert.NO_ALLOC_SPACE:
            return (
                "Every device belonging to the pool has been fully allocated. "
                "To increase the allocable space, add additional data devices "
                "to the pool."
            )

        assert False, "impossible code reached"  # pragma: no cover

    def summarize(self) -> str:
        """
        Return a short summary of the alert.
        """
        if self is PoolAllocSpaceAlert.NO_ALLOC_SPACE:
            return "All devices fully allocated"

        assert False, "impossible code reached"  # pragma: no cover


class PoolDeviceSizeChangeAlert(IntEnum):
    """
    Codes for identifying for a pool if a device that belongs to the pool has
    been detected to have increased or reduced in size.
    """

    DEVICE_SIZE_INCREASED = 1
    DEVICE_SIZE_DECREASED = 2

    def __str__(self) -> str:
        if self is PoolDeviceSizeChangeAlert.DEVICE_SIZE_INCREASED:
            return f"{Level.INFO}DS{str(self.value).zfill(3)}"

        if self is PoolDeviceSizeChangeAlert.DEVICE_SIZE_DECREASED:
            return f"{Level.WARNING}DS{str(self.value).zfill(3)}"

        assert False, "impossible code reached"  # pragma: no cover

    def explain(self) -> str:
        """
        Return an explanation of the alert.
        """
        if self is PoolDeviceSizeChangeAlert.DEVICE_SIZE_INCREASED:
            return (
                "At least one device belonging to this pool appears to have "
                "increased in size."
            )

        if self is PoolDeviceSizeChangeAlert.DEVICE_SIZE_DECREASED:
            return (
                "At least one device belonging to this pool appears to have "
                "decreased in size."
            )

        assert False, "impossible code reached"  # pragma: no cover

    def summarize(self) -> str:
        """
        Return a short summary of the alert.
        """
        if self is PoolDeviceSizeChangeAlert.DEVICE_SIZE_INCREASED:
            return "A device in this pool has increased in size."

        if self is PoolDeviceSizeChangeAlert.DEVICE_SIZE_DECREASED:
            return "A device in this pool has decreased in size."

        assert False, "impossible code reached"  # pragma: no cover


class PoolEncryptionAlert(IntEnum):
    """
    Codes for encryption problems.
    """

    VOLUME_KEY_NOT_LOADED = 1
    VOLUME_KEY_STATUS_UNKNOWN = 2

    def __str__(self) -> str:
        return f"{Level.WARNING}C{str(self.value).zfill(3)}"

    def explain(self) -> str:
        """
        Return an explanation of the alert.
        """
        if self is PoolEncryptionAlert.VOLUME_KEY_NOT_LOADED:
            return (
                "The pool's volume key is not loaded. This may result in an "
                "error if the pool's encryption layer needs to be modified. "
                "If the pool is encrypted with a key in the kernel keyring "
                "then setting that key may resolve the problem."
            )
        if self is PoolEncryptionAlert.VOLUME_KEY_STATUS_UNKNOWN:
            return (
                "The pool's volume key may or may not be loaded. If the volume "
                "key is not loaded, there may an error if the pool's "
                "encryption layer needs to be modified."
            )

        assert False, "impossible code reached"  # pragma: no cover

    def summarize(self) -> str:
        """
        Return a short summary of the alert.
        """
        if self is PoolEncryptionAlert.VOLUME_KEY_NOT_LOADED:
            return "Volume key not loaded"
        if self is PoolEncryptionAlert.VOLUME_KEY_STATUS_UNKNOWN:
            return "Volume key status unknown"

        assert False, "impossible code reached"  # pragma: no cover


CLASSES = [
    PoolAllocSpaceAlert,
    PoolDeviceSizeChangeAlert,
    PoolEncryptionAlert,
    PoolMaintenanceAlert,
]

type PoolAlertType = Union[
    PoolAllocSpaceAlert,
    PoolDeviceSizeChangeAlert,
    PoolEncryptionAlert,
    PoolMaintenanceAlert,
]


class PoolAlert:
    """
    Summary class for all pool alerts.
    """

    CODE_MAP: Dict[str, PoolAlertType] = dict(
        (str(code), code) for c in CLASSES for code in list(c)
    )

    @staticmethod
    def codes() -> List[PoolAlertType]:
        """
        Return all pool alerts.
        """
        return list(PoolAlert.CODE_MAP.values())

    @staticmethod
    def code_strs() -> List[str]:
        """
        Return str representations of all pool alerts.
        """
        return list(PoolAlert.CODE_MAP.keys())

    @staticmethod
    def from_str(
        code: str,
    ) -> Optional[PoolAlertType]:
        """
        Obtain an alert object from a distinguishing error string.

        :param str code:
        :returns: PoolAlertType
        """

        return PoolAlert.CODE_MAP.get(code)
