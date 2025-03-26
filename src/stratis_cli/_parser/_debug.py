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

from .._actions import (
    BlockdevDebugActions,
    FilesystemDebugActions,
    PoolDebugActions,
    TopDebugActions,
)
from ._shared import UUID_OR_NAME

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
            "args": [("device", {"help": "Path to device"})],
            "func": TopDebugActions.send_uevent,
        },
    ),
]

POOL_DEBUG_SUBCMDS = [
    (
        "get-object-path",
        {
            "help": "Get the object path for a pool name or UUID",
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": "Choose one option to specify the pool",
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                ),
            ],
            "func": PoolDebugActions.get_object_path,
        },
    ),
    (
        "get-metadata",
        {
            "args": [
                (
                    "--pretty",
                    {
                        "action": "store_true",
                        "help": "Format output string prettily",
                    },
                ),
                (
                    "--written",
                    {
                        "action": "store_true",
                        "help": "Read the metadata most recently written",
                    },
                ),
            ],
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": "Choose one option to specify the pool",
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                ),
            ],
            "help": "Report the pool's metadata",
            "func": PoolDebugActions.get_metadata,
        },
    ),
]

FILESYSTEM_DEBUG_SUBCMDS = [
    (
        "get-object-path",
        {
            "help": "Get the object path for a filesystem name or UUID",
            "groups": [
                (
                    "Filesystem Identifier",
                    {
                        "description": "Choose one option to specify the filesystem",
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                ),
            ],
            "func": FilesystemDebugActions.get_object_path,
        },
    ),
    (
        "get-metadata",
        {
            "help": (
                "Get the filesystem metadata for all filesystems belonging to "
                "the specified pool"
            ),
            "args": [
                ("pool_name", {"help": "Pool name"}),
                (
                    "--pretty",
                    {
                        "action": "store_true",
                        "help": "Format output string prettily",
                    },
                ),
                (
                    "--written",
                    {
                        "action": "store_true",
                        "help": "Read the metadata most recently written",
                    },
                ),
                ("--fs-name", {"help": "Optional filesystem name"}),
            ],
            "func": FilesystemDebugActions.get_metadata,
        },
    ),
]

BLOCKDEV_DEBUG_SUBCMDS = [
    (
        "get-object-path",
        {
            "help": "Get the object path for a blockdev UUID",
            "groups": [
                (
                    "Block Device Identifier",
                    {
                        "description": (
                            "Choose one option to specify the block device"
                        ),
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                ),
            ],
            "func": BlockdevDebugActions.get_object_path,
        },
    ),
]
