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
Debugging commands for pool
"""

# isort: STDLIB
from uuid import UUID

from .._actions import (
    BlockdevDebugActions,
    FilesystemDebugActions,
    PoolDebugActions,
    TopDebugActions,
)

TOP_DEBUG_SUBCMDS = [
    (
        "refresh",
        {
            "help": "Refresh all un-stopped pools.",
            "func": TopDebugActions.refresh_state,
        },
    ),
    (
        "uevent",
        {
            "help": "Generate a synthetic uevent.",
            "args": [("device", {"action": "store", "help": "Path to device"})],
            "func": TopDebugActions.send_uevent,
        },
    ),
]

POOL_DEBUG_SUBCMDS = [
    (
        "get-object-path",
        {
            "help": "Get the object path for a pool name or UUID",
            "mut_ex_args": [
                (
                    True,
                    [
                        (
                            "--name",
                            {
                                "action": "store",
                                "help": "Name of pool",
                                "dest": "name",
                            },
                        ),
                        (
                            "--uuid",
                            {
                                "action": "store",
                                "help": "UUID of pool",
                                "dest": "uuid",
                                "type": UUID,
                            },
                        ),
                    ],
                )
            ],
            "func": PoolDebugActions.get_object_path,
        },
    ),
]

FILESYSTEM_DEBUG_SUBCMDS = [
    (
        "get-object-path",
        {
            "help": "Get the object path for a filesystem name or UUID",
            "mut_ex_args": [
                (
                    True,
                    [
                        (
                            "--name",
                            {
                                "action": "store",
                                "help": "Name of filesystem",
                                "dest": "name",
                            },
                        ),
                        (
                            "--uuid",
                            {
                                "action": "store",
                                "help": "UUID of filesystem",
                                "dest": "uuid",
                                "type": UUID,
                            },
                        ),
                    ],
                )
            ],
            "func": FilesystemDebugActions.get_object_path,
        },
    ),
]

BLOCKDEV_DEBUG_SUBCMDS = [
    (
        "get-object-path",
        {
            "help": "Get the object path for a blockdev UUID",
            "mut_ex_args": [
                (
                    True,
                    [
                        (
                            "--uuid",
                            {
                                "action": "store",
                                "help": "UUID of filesystem",
                                "dest": "uuid",
                                "type": UUID,
                            },
                        ),
                    ],
                )
            ],
            "func": BlockdevDebugActions.get_object_path,
        },
    ),
]
