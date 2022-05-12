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
from enum import IntEnum


class PoolMaintenanceErrorCode(IntEnum):
    """
    Maintenance error codes for the pool.
    """

    NO_IPC_REQUESTS = 1
    NO_POOL_CHANGES = 2

    def __str__(self):
        return f"EM{str(self.value).zfill(3)}"

    @staticmethod
    def from_str(code_str):
        """
        Discover the code, if any, from the code string.

        :returns: the code if it finds a match, otherwise None
        :rtype: PoolMaintenanceErrorCode or NoneType
        """
        return next(
            (code for code in PoolMaintenanceErrorCode if code_str == str(code)), None
        )

    def explain(self):
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

        if self is PoolMaintenanceErrorCode.NO_POOL_CHANGES:  # pragma: no cover
            return (
                "The pool is unable to manage itself by reacting to events, "
                "such as devicemapper events, that might require it to take "
                "any maintenance operations."
            )

        assert False, "impossible error code reached"  # pragma: no cover


class PoolAllocSpaceErrorCode(IntEnum):
    """
    Code if the pool has run out of space to allocate.
    """

    NO_ALLOC_SPACE = 1

    def __str__(self):
        return f"WS{str(self.value).zfill(3)}"

    def explain(self):
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

    @staticmethod
    def from_str(code_str):
        """
        Discover the code, if any, from the code string.

        :returns: the code if it finds a match, otherwise None
        :rtype: PoolAllocSpaceErrorCode or NoneType
        """
        return next(
            (code for code in PoolAllocSpaceErrorCode if code_str == str(code)), None
        )


class PoolErrorCode:
    """
    Summary class for all pool error codes.
    """

    CLASSES = [PoolMaintenanceErrorCode, PoolAllocSpaceErrorCode]

    @staticmethod
    def codes():
        """
        Return all pool error codes.
        """
        return [code for c in PoolErrorCode.CLASSES for code in list(c)]

    @staticmethod
    def error_from_str(error_code):
        """
        Obtain an error object from a distinguishing error string.

        :param str error_code:
        :returns: error object
        :raises: StopIteration if no match found
        """
        return next(
            (
                code
                for code in (c.from_str(error_code) for c in PoolErrorCode.CLASSES)
                if code is not None
            )
        )

    @staticmethod
    def explain(error_code):
        """
        Return explanation for error code, else None.

        :param str error_code:
        """
        return PoolErrorCode.error_from_str(error_code).explain()
