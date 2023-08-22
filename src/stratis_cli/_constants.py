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

    def __str__(self):
        return self.value

    def __bool__(self):
        return self is YesOrNo.YES

    @staticmethod
    def from_str(code_str):
        """
        From a string code, return the YesOrNo value.

        :param str code_str: the string code
        :returns: the YesOrNo value
        :rtype: YesOrNo
        :raises: StopIteration
        """
        return next(item for item in YesOrNo if code_str == str(item))


class PoolIdType(Enum):
    """
    Whether the pool identifier is a UUID or a name.
    """

    UUID = 0
    NAME = 1
