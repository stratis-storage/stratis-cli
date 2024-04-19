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
Definition of filesystem actions to display in the CLI.
"""

from .._actions import LogicalActions
from ._debug import FILESYSTEM_DEBUG_SUBCMDS
from ._range import parse_range


def parse_range_or_current(values):
    """
    Allow specifying a Range or the value "current". Include the original
    value specified by the user as well as the Range result if the user
    specified a valid range. This is purely useful for error messages,
    so that an error message will contain what the user specified if there
    needs to be reported an idempotency error.
    """
    return (None if values == "current" else parse_range(values), values)


LOGICAL_SUBCMDS = [
    (
        "create",
        {
            "help": "Create filesystems in a pool",
            "args": [
                ("pool_name", {"help": "pool name"}),
                (
                    "fs_name",
                    {
                        "help": "Create filesystems in this pool using the given names",
                        "nargs": "+",
                    },
                ),
                (
                    "--size",
                    {
                        "dest": "size",
                        "help": 'The size of the filesystems to be created, e.g., "32GiB"',
                        "type": parse_range,
                    },
                ),
                (
                    "--size-limit",
                    {
                        "dest": "size_limit",
                        "help": 'An upper limit on the size of filesystems, e.g., "2TiB"',
                        "type": parse_range,
                    },
                ),
            ],
            "func": LogicalActions.create_volumes,
        },
    ),
    (
        "snapshot",
        {
            "help": "Snapshot the named filesystem in a pool",
            "args": [
                ("pool_name", {"help": "pool name"}),
                ("origin_name", {"help": "origin name"}),
                ("snapshot_name", {"help": "snapshot name"}),
            ],
            "func": LogicalActions.snapshot_filesystem,
        },
    ),
    (
        "list",
        {
            "help": "List filesystems",
            "args": [
                (
                    "pool_name",
                    {
                        "nargs": "?",
                        "help": "Pool name",
                    },
                )
            ],
            "func": LogicalActions.list_volumes,
        },
    ),
    (
        "destroy",
        {
            "help": "Destroy filesystems in a pool",
            "args": [
                ("pool_name", {"help": "pool name"}),
                (
                    "fs_name",
                    {
                        "help": "Destroy the named filesystems in this pool",
                        "nargs": "+",
                    },
                ),
            ],
            "func": LogicalActions.destroy_volumes,
        },
    ),
    (
        "rename",
        {
            "help": "Rename a filesystem",
            "args": [
                (
                    "pool_name",
                    {
                        "help": "Name of the pool the filesystem is part of",
                    },
                ),
                (
                    "fs_name",
                    {"help": "Name of the filesystem to change"},
                ),
                (
                    "new_name",
                    {"help": "New name to give that filesystem"},
                ),
            ],
            "func": LogicalActions.rename_fs,
        },
    ),
    (
        "set-size-limit",
        {
            "help": "set limit for this filesystem",
            "args": [
                (
                    "pool_name",
                    {
                        "help": "Name of the pool the filesystem is part of",
                    },
                ),
                (
                    "fs_name",
                    {"help": "Name of the filesystem to change"},
                ),
                (
                    "limit",
                    {
                        "help": (
                            "Upper limit on size of filesystem. Use the "
                            'keyword "current" to specify the current size of '
                            "the filesystem."
                        ),
                        "type": parse_range_or_current,
                    },
                ),
            ],
            "func": LogicalActions.set_size_limit,
        },
    ),
    (
        "unset-size-limit",
        {
            "help": "unset size limit for this filesystem",
            "args": [
                (
                    "pool_name",
                    {
                        "help": "Name of the pool the filesystem is part of",
                    },
                ),
                (
                    "fs_name",
                    {"help": "Name of the filesystem to change"},
                ),
            ],
            "func": LogicalActions.unset_size_limit,
        },
    ),
    (
        "debug",
        {
            "help": ("Miscellaneous filesystem-level debug commands"),
            "subcmds": FILESYSTEM_DEBUG_SUBCMDS,
        },
    ),
]
