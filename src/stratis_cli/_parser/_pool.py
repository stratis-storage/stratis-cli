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
Definition of pool actions to display in the CLI.
"""

# isort: STDLIB
from argparse import ArgumentTypeError
from uuid import UUID

from .._actions import BindActions, PoolActions
from .._constants import Clevis, EncryptionMethod, YesOrNo
from .._error_codes import PoolErrorCode
from ._bind import BIND_SUBCMDS, REBIND_SUBCMDS
from ._debug import POOL_DEBUG_SUBCMDS


def _ensure_nat(arg):
    """
    Raise error if argument is not an natural number.
    """
    try:
        result = int(arg)
    except Exception as err:
        raise ArgumentTypeError(f"Argument {arg} is not a natural number.") from err

    if result < 0:
        raise ArgumentTypeError(f"Argument {arg} is not a natural number.")
    return result


POOL_SUBCMDS = [
    (
        "create",
        {
            "help": "Create a pool",
            "groups": [
                (
                    "clevis",
                    {
                        "description": "Arguments controlling creation with Clevis encryption",
                        "args": [
                            (
                                "--clevis",
                                {
                                    "type": Clevis,
                                    "help": ("Specification for binding with Clevis."),
                                    "choices": list(Clevis),
                                },
                            ),
                            (
                                "--tang-url",
                                {
                                    "help": (
                                        "URL of Clevis tang server "
                                        "(--clevis=[tang|nbde] must be set)"
                                    ),
                                },
                            ),
                        ],
                        "mut_ex_args": [
                            (
                                False,
                                [
                                    (
                                        "--trust-url",
                                        {
                                            "action": "store_true",
                                            "help": (
                                                "Omit verification of tang "
                                                "server credentials "
                                                "(--tang-url option must be "
                                                "set)"
                                            ),
                                        },
                                    ),
                                    (
                                        "--thumbprint",
                                        {
                                            "help": (
                                                "Thumbprint of tang server "
                                                "(--tang-url option must be "
                                                "set)"
                                            ),
                                        },
                                    ),
                                ],
                            )
                        ],
                    },
                )
            ],
            "args": [
                ("pool_name", {"help": "Name of new pool"}),
                (
                    "blockdevs",
                    {"help": "Create the pool using these block devs", "nargs": "+"},
                ),
                (
                    "--key-desc",
                    {
                        "help": (
                            "Key description of key in kernel keyring to use "
                            "for encryption"
                        ),
                    },
                ),
                (
                    "--no-overprovision",
                    {
                        "action": "store_true",
                        "help": (
                            "Do not allow the sum of the logical size of the "
                            "pool's filesystems to exceed the size of the "
                            "pool's data area."
                        ),
                    },
                ),
            ],
            "func": PoolActions.create_pool,
        },
    ),
    (
        "stop",
        {
            "help": (
                "Stop a pool. Tear down the pool's storage stack "
                "but do not erase any metadata."
            ),
            "mut_ex_args": [
                (
                    True,
                    [
                        (
                            "--uuid",
                            {
                                "type": UUID,
                                "help": "UUID of the pool to stop",
                            },
                        ),
                        (
                            "--name",
                            {"help": "name of the pool to stop"},
                        ),
                    ],
                )
            ],
            "func": PoolActions.stop_pool,
        },
    ),
    (
        "start",
        {
            "help": "Start a pool.",
            "mut_ex_args": [
                (
                    True,
                    [
                        (
                            "--uuid",
                            {
                                "type": UUID,
                                "help": "UUID of the pool to start",
                            },
                        ),
                        (
                            "--name",
                            {"help": "name of the pool to start"},
                        ),
                    ],
                )
            ],
            "args": [
                (
                    "--unlock-method",
                    {
                        "choices": list(EncryptionMethod),
                        "help": "Method to use to unlock the pool if encrypted.",
                        "type": EncryptionMethod,
                    },
                ),
            ],
            "func": PoolActions.start_pool,
        },
    ),
    (
        "init-cache",
        {
            "help": "Initialize the cache with block devices",
            "args": [
                (
                    "pool_name",
                    {
                        "help": ("Name of the pool for which to initialize the cache"),
                    },
                ),
                (
                    "blockdevs",
                    {
                        "help": "Initialize the pool cache using these block devs",
                        "nargs": "+",
                    },
                ),
            ],
            "func": PoolActions.init_cache,
        },
    ),
    (
        "list",
        {
            "help": "List pools",
            "description": "List Stratis pools",
            "mut_ex_args": [
                (
                    False,
                    [
                        (
                            "--uuid",
                            {
                                "type": UUID,
                                "help": "UUID of pool to list",
                            },
                        ),
                        (
                            "--name",
                            {
                                "help": "name of pool to list",
                            },
                        ),
                    ],
                ),
            ],
            "args": [
                (
                    "--stopped",
                    {
                        "action": "store_true",
                        "help": "Display information about stopped pools only.",
                    },
                ),
            ],
            "func": PoolActions.list_pools,
        },
    ),
    (
        "destroy",
        {
            "help": "Destroy a pool",
            "args": [("pool_name", {"help": "pool name"})],
            "func": PoolActions.destroy_pool,
        },
    ),
    (
        "rename",
        {
            "help": "Rename a pool",
            "args": [
                ("current", {"help": "Current pool name"}),
                ("new", {"help": "New pool name"}),
            ],
            "func": PoolActions.rename_pool,
        },
    ),
    (
        "add-data",
        {
            "help": "Add one or more blockdevs to an existing pool for use as data storage",
            "args": [
                ("pool_name", {"help": "Pool name"}),
                (
                    "blockdevs",
                    {
                        "help": "Block devices to add to the pool",
                        "metavar": "blockdev",
                        "nargs": "+",
                    },
                ),
            ],
            "func": PoolActions.add_data_devices,
        },
    ),
    (
        "add-cache",
        {
            "help": "Add one or more blockdevs to an existing pool for use as cache",
            "args": [
                ("pool_name", {"help": "Pool name"}),
                (
                    "blockdevs",
                    {
                        "help": "Block devices to add to the pool as cache",
                        "metavar": "blockdev",
                        "nargs": "+",
                    },
                ),
            ],
            "func": PoolActions.add_cache_devices,
        },
    ),
    (
        "extend-data",
        {
            "help": (
                "Extend the pool's data capacity with additional storage "
                "space offered by its component data devices through, e.g., "
                "expansion of a component RAID device."
            ),
            "args": [
                ("pool_name", {"help": "Pool name"}),
                (
                    "--device-uuid",
                    {
                        "action": "extend",
                        "nargs": "*",
                        "type": UUID,
                        "default": [],
                        "help": (
                            "UUID of device to use; may be specified multiple "
                            "times. If no devices are specified then all "
                            "devices belonging to the pool that appear to have "
                            "increased in size will be used."
                        ),
                    },
                ),
            ],
            "func": PoolActions.extend_data,
        },
    ),
    (
        "bind",
        {
            "help": "Bind the given pool with an additional encryption facility",
            "subcmds": BIND_SUBCMDS,
        },
    ),
    (
        "rebind",
        {
            "help": (
                "Rebind the given pool with a currently in use encryption "
                "facility but new credentials"
            ),
            "subcmds": REBIND_SUBCMDS,
        },
    ),
    (
        "unbind",
        {
            "help": "Unbind the given pool, removing support for encryption with Clevis",
            "args": [
                (
                    "method",
                    {
                        "choices": list(EncryptionMethod),
                        "help": "Encryption method to unbind",
                        "type": EncryptionMethod,
                    },
                ),
                ("pool_name", {"help": "Pool name"}),
            ],
            "func": BindActions.unbind,
        },
    ),
    (
        "set-fs-limit",
        {
            "help": "Set the maximum number of filesystems the pool can support.",
            "args": [
                ("pool_name", {"help": "Pool name"}),
                (
                    "amount",
                    {
                        "type": _ensure_nat,
                        "help": "Number of filesystems.",
                    },
                ),
            ],
            "func": PoolActions.set_fs_limit,
        },
    ),
    (
        "overprovision",
        {
            "help": "Specify whether or not to allow overprovisioning for the pool.",
            "args": [
                ("pool_name", {"help": "Pool name"}),
                (
                    "decision",
                    {
                        "help": "yes to allow overprovisioning, otherwise no",
                        "choices": list(YesOrNo),
                        "type": YesOrNo,
                    },
                ),
            ],
            "func": PoolActions.set_overprovisioning_mode,
        },
    ),
    (
        "explain",
        {
            "help": "Explain pool alert codes",
            "args": [
                (
                    "code",
                    {
                        "choices": [str(x) for x in PoolErrorCode.codes()],
                        "help": "Error code to explain",
                    },
                )
            ],
            "func": PoolActions.explain_code,
        },
    ),
    (
        "debug",
        {
            "help": ("Miscellaneous pool-level debug commands"),
            "subcmds": POOL_DEBUG_SUBCMDS,
        },
    ),
]
