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
import copy
from argparse import SUPPRESS
from uuid import UUID

# isort: THIRDPARTY
from justbytes import MiB, Range

from .._actions import BindActions, PoolActions
from .._constants import (
    Clevis,
    EncryptionMethod,
    IntegrityOption,
    IntegrityTagSpec,
    UnlockMethod,
    YesOrNo,
)
from .._error_codes import PoolErrorCode
from ._debug import POOL_DEBUG_SUBCMDS
from ._encryption import BIND_SUBCMDS, REBIND_SUBCMDS
from ._shared import (
    KEYFILE_PATH_OR_STDIN,
    TRUST_URL_OR_THUMBPRINT,
    UUID_OR_NAME,
    ClevisEncryptionOptions,
    DefaultAction,
    RejectAction,
    ensure_nat,
    parse_range,
)


class IntegrityOptions:  # pylint: disable=too-few-public-methods
    """
    Gathers and verifies integrity options.
    """

    def __init__(self, namespace):
        self.integrity = copy.copy(namespace.integrity)
        del namespace.integrity

        self.journal_size = copy.copy(namespace.journal_size)
        del namespace.journal_size

        self.journal_size_default = getattr(namespace, "journal_size_default", True)

        self.tag_spec = copy.copy(namespace.tag_spec)
        del namespace.tag_spec

        self.tag_spec_default = getattr(namespace, "tag_spec_default", True)

    def verify(self, namespace, parser):
        """
        Do supplementary parsing of conditional arguments.
        """

        if self.integrity is IntegrityOption.NO and not self.journal_size_default:
            parser.error(
                f'--integrity value "{IntegrityOption.NO}" and --journal-size '
                "option can not be specified together"
            )

        if self.integrity is IntegrityOption.NO and not self.tag_spec_default:
            parser.error(
                f'--integrity value "{IntegrityOption.NO}" and --tag-spec '
                "option can not be specified together"
            )

        namespace.integrity = self


class CreateOptions:  # pylint: disable=too-few-public-methods
    """
    Gathers and verifies options specified on pool create.
    """

    def __init__(self, namespace):
        self.clevis_encryption_options = ClevisEncryptionOptions(namespace)
        self.integrity_options = IntegrityOptions(namespace)

    def verify(self, namespace, parser):
        """
        Verify that create command-line is formed correctly.
        """
        self.clevis_encryption_options.verify(namespace, parser)
        self.integrity_options.verify(namespace, parser)


POOL_SUBCMDS = [
    (
        "create",
        {
            "help": "Create a pool",
            "groups": [
                (
                    "Encryption",
                    {
                        "description": "Arguments controlling creation with encryption",
                        "args": [
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
                                "--clevis",
                                {
                                    "type": Clevis,
                                    "help": "Specification for binding with Clevis.",
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
                    },
                ),
                (
                    "Tang Server Verification (only if --tang-url option is set)",
                    {
                        "description": "Choose one option",
                        "mut_ex_args": [(False, TRUST_URL_OR_THUMBPRINT)],
                    },
                ),
                (
                    "Integrity",
                    {
                        "description": (
                            "Optional parameters for configuring integrity "
                            "metadata pre-allocation"
                        ),
                        "args": [
                            (
                                "--integrity",
                                {
                                    "help": (
                                        "Integrity options for this pool. If "
                                        f'"{IntegrityOption.NO}" no space will '
                                        "be allocated for integrity metadata "
                                        "and it will never be possible to turn "
                                        "on integrity functionality for this "
                                        "pool. "
                                        f'If "{IntegrityOption.PRE_ALLOCATE}" '
                                        "then space will be allocated for "
                                        "integrity metadata and it will be "
                                        "possible to switch on integrity "
                                        "functionality in future. The default "
                                        'is "%(default)s".'
                                    ),
                                    "choices": list(IntegrityOption),
                                    "default": IntegrityOption.PRE_ALLOCATE,
                                    "type": IntegrityOption,
                                },
                            ),
                            (
                                "--journal-size",
                                {
                                    "help": (
                                        "Size of integrity device's journal. "
                                        "Each block is written to this journal "
                                        "before being written to its address. "
                                        "The default is %(default)s."
                                    ),
                                    "action": DefaultAction,
                                    "default": Range(128, MiB),
                                    "type": parse_range,
                                },
                            ),
                            (
                                "--tag-spec",
                                {
                                    "help": (
                                        "Integrity tag specification defining "
                                        "the size of the tag used to store a "
                                        "checksum or other value for each "
                                        "block on a device. All size "
                                        "specifications are in bits. The "
                                        "default is %(default)s."
                                    ),
                                    "action": DefaultAction,
                                    "default": IntegrityTagSpec.B512,
                                    "choices": [
                                        x
                                        for x in list(IntegrityTagSpec)
                                        if x is not IntegrityTagSpec.B0
                                    ],
                                    "type": IntegrityTagSpec,
                                },
                            ),
                        ],
                    },
                ),
            ],
            "args": [
                (
                    "--post-parser",
                    {
                        "action": RejectAction,
                        "default": CreateOptions,
                        "help": SUPPRESS,
                        "nargs": "?",
                    },
                ),
                ("pool_name", {"help": "Name of new pool"}),
                (
                    "blockdevs",
                    {"help": "Create the pool using these block devs", "nargs": "+"},
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
        "destroy",
        {
            "help": "Destroy a pool",
            "args": [("pool_name", {"help": "pool name"})],
            "func": PoolActions.destroy_pool,
        },
    ),
    (
        "start",
        {
            "help": "Start a pool.",
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": (
                            "Choose one option to specify the pool to start"
                        ),
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                ),
                (
                    "Optional Unlock Method",
                    {
                        "description": (
                            "Choose one option to specify an unlock method if "
                            "the pool is encrypted"
                        ),
                        "mut_ex_args": [
                            (
                                False,
                                [
                                    (
                                        "--unlock-method",
                                        {
                                            "choices": list(UnlockMethod),
                                            "help": "Method to use to unlock the pool",
                                            "type": UnlockMethod,
                                        },
                                    ),
                                    (
                                        "--token-slot",
                                        {
                                            "help": (
                                                "token slot; alternative way of specifying "
                                                "an unlock method; for V2 pools only"
                                            ),
                                            "type": ensure_nat,
                                        },
                                    ),
                                ],
                            ),
                        ],
                    },
                ),
                (
                    "Optional Key Value Specification",
                    {
                        "description": (
                            "Choose one option to specify a key value if the "
                            "pool is encrypted and no unattended decryption "
                            "mechanism is available"
                        ),
                        "mut_ex_args": [
                            (False, KEYFILE_PATH_OR_STDIN),
                        ],
                    },
                ),
            ],
            "func": PoolActions.start_pool,
        },
    ),
    (
        "stop",
        {
            "help": (
                "Stop a pool. Tear down the pool's storage stack "
                "but do not erase any metadata."
            ),
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": (
                            "Choose one option to specify the pool to stop"
                        ),
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                ),
            ],
            "func": PoolActions.stop_pool,
        },
    ),
    (
        "list",
        {
            "help": "List pools",
            "description": "List Stratis pools",
            "args": [
                (
                    "--stopped",
                    {
                        "action": "store_true",
                        "help": "Display information about stopped pools only.",
                    },
                ),
            ],
            "groups": [
                (
                    "Optional Pool Identifier",
                    {
                        "description": (
                            "Choose one option to display a detailed listing "
                            "for a single pool"
                        ),
                        "mut_ex_args": [
                            (False, UUID_OR_NAME),
                        ],
                    },
                ),
            ],
            "func": PoolActions.list_pools,
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
        "init-cache",
        {
            "help": "Initialize the cache with block devices",
            "args": [
                (
                    "pool_name",
                    {
                        "help": "Name of the pool for which to initialize the cache",
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
            "help": "Unbind the given pool, removing use of the specified encryption method",
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
                (
                    "--token-slot",
                    {
                        "help": (
                            "token slot; must be specified if there is more "
                            "than one binding with the specified method"
                        ),
                        "type": ensure_nat,
                    },
                ),
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
                        "type": ensure_nat,
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
                        "choices": PoolErrorCode.code_strs(),
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
            "help": "Miscellaneous pool-level debug commands",
            "subcmds": POOL_DEBUG_SUBCMDS,
        },
    ),
]
