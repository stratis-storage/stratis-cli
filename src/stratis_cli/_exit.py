# Copyright 2020 Red Hat, Inc.
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
Exit codes and methods.
"""
# isort: STDLIB
import os
import sys
from enum import IntEnum


class StratisCliErrorCodes(IntEnum):
    """
    StratisCli Error Codes
    """

    OK = 0
    ERROR = 1
    PARSE_ERROR = 2


def exit_(code: StratisCliErrorCodes, msg: str):
    """
    Exits program with a given exit code and error message.
    """
    print(msg, os.linesep, file=sys.stderr, flush=True)
    raise SystemExit(code)
