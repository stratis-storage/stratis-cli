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
from enum import IntEnum


class PoolMaintenanceErrorCode(IntEnum):
    """
    Maintenance error codes for the pool.
    """

    NO_IPC_REQUESTS = 1
    NO_POOL_CHANGES = 2
    READ_ONLY = 3

    def __str__(self):
        return "EM%s" % str(self.value).zfill(3)

    @staticmethod
    def from_str(code_str):
        """
        Discover the code, if any, from the code string.

        :returns: the code if it finds a match, otherwise None
        :rtype: PoolMaintenanceErrorCode or NoneType
        """
        for code in PoolMaintenanceErrorCode:
            if code_str == str(code):
                return code
        return None

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

        if self is PoolMaintenanceErrorCode.NO_POOL_CHANGES:
            return (
                "The pool is unable to manage itself by reacting to events, "
                "such as devicemapper events, that might require it to take "
                "any maintenance operations."
            )

        if self is PoolMaintenanceErrorCode.READ_ONLY:  # pragma: no cover
            return "The pool is in read-only mode."

        assert False, "impossible error code reached"  # pragma: no cover
