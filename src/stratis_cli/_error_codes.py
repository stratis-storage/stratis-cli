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


class PoolMaintenanceErrorCode(IntEnum):
    """
    Maintenance error codes for the pool.
    """

    NO_IPC_REQUESTS = 1
    NO_POOL_CHANGES = 2

    def __str__(self) -> str:
        return f"{Level.ERROR}M{str(self.value).zfill(3)}"

    def explain(self) -> str:
        """
        Return an explanation of the error return code.
        """
        if self is PoolMaintenanceErrorCode.NO_IPC_REQUESTS:
            return (
                "The pool will return an error on any IPC request that could "
                "cause a change in the pool state, for example, a request to "
                "rename a filesystem. It will still be able to respond to "
                "purely informational requests."
            )

        if self is PoolMaintenanceErrorCode.NO_POOL_CHANGES:
            return (
                "The pool is unable to manage itself by reacting to events, "
                "such as devicemapper events, that might require it to take "
                "any maintenance operations."
            )

        assert False, "impossible error code reached"  # pragma: no cover

    def summarize(self) -> str:
        """
        Return a short summary of the return code.
        """
        if self is PoolMaintenanceErrorCode.NO_IPC_REQUESTS:
            return "Pool state changes not possible"

        if self is PoolMaintenanceErrorCode.NO_POOL_CHANGES:
            return "Pool maintenance operations not possible"

        assert False, "impossible error code reached"  # pragma: no cover


class PoolAllocSpaceErrorCode(IntEnum):
    """
    Code if the pool has run out of space to allocate.
    """

    NO_ALLOC_SPACE = 1

    def __str__(self) -> str:
        return f"{Level.WARNING}S{str(self.value).zfill(3)}"

    def explain(self) -> str:
        """
        Return an explanation of the return code.
        """
        if self is PoolAllocSpaceErrorCode.NO_ALLOC_SPACE:
            return (
                "Every device belonging to the pool has been fully allocated. "
                "To increase the allocable space, add additional data devices "
                "to the pool."
            )

        assert False, "impossible error code reached"  # pragma: no cover

    def summarize(self) -> str:
        """
        Return a short summary of the return code.
        """
        if self is PoolAllocSpaceErrorCode.NO_ALLOC_SPACE:
            return "All devices fully allocated"

        assert False, "impossible error code reached"  # pragma: no cover


class PoolDeviceSizeChangeCode(IntEnum):
    """
    Codes for identifying for a pool if a device that belongs to the pool has
    been detected to have increased or reduced in size.
    """

    DEVICE_SIZE_INCREASED = 1
    DEVICE_SIZE_DECREASED = 2

    def __str__(self) -> str:
        if self is PoolDeviceSizeChangeCode.DEVICE_SIZE_INCREASED:
            return f"{Level.INFO}DS{str(self.value).zfill(3)}"

        if self is PoolDeviceSizeChangeCode.DEVICE_SIZE_DECREASED:
            return f"{Level.WARNING}DS{str(self.value).zfill(3)}"

        assert False, "impossible error code reached"  # pragma: no cover

    def explain(self) -> str:
        """
        Return an explanation of the return code.
        """
        if self is PoolDeviceSizeChangeCode.DEVICE_SIZE_INCREASED:
            return (
                "At least one device belonging to this pool appears to have "
                "increased in size."
            )

        if self is PoolDeviceSizeChangeCode.DEVICE_SIZE_DECREASED:
            return (
                "At least one device belonging to this pool appears to have "
                "decreased in size."
            )

        assert False, "impossible error code reached"  # pragma: no cover

    def summarize(self) -> str:
        """
        Return a short summary of the return code.
        """
        if self is PoolDeviceSizeChangeCode.DEVICE_SIZE_INCREASED:
            return "A device in this pool has increased in size."

        if self is PoolDeviceSizeChangeCode.DEVICE_SIZE_DECREASED:
            return "A device in this pool has decreased in size."

        assert False, "impossible error code reached"  # pragma: no cover


class PoolEncryptionErrorCode(IntEnum):
    """
    Codes for encryption problems.
    """

    VOLUME_KEY_NOT_LOADED = 1
    VOLUME_KEY_STATUS_UNKNOWN = 2

    def __str__(self) -> str:
        return f"{Level.WARNING}C{str(self.value).zfill(3)}"

    def explain(self) -> str:
        """
        Return an explanation of the return code.
        """
        if self is PoolEncryptionErrorCode.VOLUME_KEY_NOT_LOADED:
            return (
                "The pool's volume key is not loaded. This may result in an "
                "error if the pool's encryption layer needs to be modified. "
                "If the pool is encrypted with a key in the kernel keyring "
                "then setting that key may resolve the problem."
            )
        if self is PoolEncryptionErrorCode.VOLUME_KEY_STATUS_UNKNOWN:
            return (
                "The pool's volume key may or may not be loaded. If the volume "
                "key is not loaded, there may an error if the pool's "
                "encryption layer needs to be modified."
            )

        assert False, "impossible error code reached"  # pragma: no cover

    def summarize(self) -> str:
        """
        Return a short summary of the return code.
        """
        if self is PoolEncryptionErrorCode.VOLUME_KEY_NOT_LOADED:
            return "Volume key not loaded"
        if self is PoolEncryptionErrorCode.VOLUME_KEY_STATUS_UNKNOWN:
            return "Volume key status unknown"

        assert False, "impossible error code reached"  # pragma: no cover


CLASSES = [
    PoolAllocSpaceErrorCode,
    PoolDeviceSizeChangeCode,
    PoolEncryptionErrorCode,
    PoolMaintenanceErrorCode,
]

type PoolErrorCodeType = Union[
    PoolAllocSpaceErrorCode,
    PoolDeviceSizeChangeCode,
    PoolEncryptionErrorCode,
    PoolMaintenanceErrorCode,
]


class PoolErrorCode:
    """
    Summary class for all pool error codes.
    """

    CODE_MAP: Dict[str, PoolErrorCodeType] = dict(
        (str(code), code) for c in CLASSES for code in list(c)
    )

    @staticmethod
    def codes() -> List[PoolErrorCodeType]:
        """
        Return all pool error codes.
        """
        return list(PoolErrorCode.CODE_MAP.values())

    @staticmethod
    def code_strs() -> List[str]:
        """
        Return str representations of all pool error codes.
        """
        return list(PoolErrorCode.CODE_MAP.keys())

    @staticmethod
    def error_from_str(
        error_code: str,
    ) -> Optional[PoolErrorCodeType]:
        """
        Obtain an error object from a distinguishing error string.

        :param str error_code:
        :returns: error object
        """

        return PoolErrorCode.CODE_MAP.get(error_code)
