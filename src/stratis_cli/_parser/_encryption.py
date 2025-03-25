# Copyright 2025 Red Hat, Inc.
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
Encryption command-line parser for Stratis CLI.
"""

# isort: STDLIB
import copy
from argparse import SUPPRESS, Namespace

from .._actions import BindActions, CryptActions, RebindActions
from .._constants import Clevis, EncryptionMethod
from ._shared import (
    CLEVIS_AND_KERNEL,
    TRUST_URL_OR_THUMBPRINT,
    UUID_OR_NAME,
    ClevisEncryptionOptions,
    MoveNotice,
    RejectAction,
    ensure_nat,
)


class ClevisEncryptionOptionsForTang(
    ClevisEncryptionOptions
):  # pylint: disable=too-few-public-methods
    """
    Class that verifies Clevis encryption options for bind subcommand.
    """

    def __init__(self, namespace: Namespace):
        namespace.clevis = Clevis.TANG
        namespace.tang_url = copy.copy(namespace.url)
        del namespace.url  # pyright: ignore [reportAttributeAccessIssue]
        super().__init__(namespace)


class ClevisEncryptionOptionsForTpm2(
    ClevisEncryptionOptions
):  # pylint: disable=too-few-public-methods
    """
    Class that verifies Clevis encryption options for bind subcommand.
    """

    def __init__(self, namespace: Namespace):
        namespace.clevis = Clevis.TPM2
        namespace.thumbprint = None
        namespace.tang_url = None
        namespace.trust_url = None
        super().__init__(namespace)


BIND_SUBCMDS = [
    (
        str(Clevis.NBDE),
        {
            "help": "Bind using NBDE via a tang server",
            "args": [
                (
                    "--post-parser",
                    {
                        "action": RejectAction,
                        "default": ClevisEncryptionOptionsForTang,
                        "help": SUPPRESS,
                        "nargs": "?",
                    },
                ),
                ("pool_name", {"help": "Pool name"}),
                ("url", {"help": "URL of tang server"}),
            ],
            "groups": [
                (
                    "Tang Server Verification",
                    {
                        "description": "Choose one option",
                        "mut_ex_args": [(True, TRUST_URL_OR_THUMBPRINT)],
                    },
                )
            ],
            "aliases": [str(Clevis.TANG)],
            "epilog": str(
                MoveNotice("nbde", "pool bind", "pool encryption bind", "3.10.0")
            ),
            "func": BindActions.bind_clevis,
        },
    ),
    (
        str(Clevis.TPM2),
        {
            "help": "Bind using TPM2",
            "args": [
                (
                    "--post-parser",
                    {
                        "action": RejectAction,
                        "default": ClevisEncryptionOptionsForTpm2,
                        "help": SUPPRESS,
                        "nargs": "?",
                    },
                ),
                ("pool_name", {"help": "Pool name"}),
            ],
            "epilog": str(
                MoveNotice("tpm2", "pool bind", "pool encryption bind", "3.10.0")
            ),
            "func": BindActions.bind_clevis,
        },
    ),
    (
        "keyring",
        {
            "help": "Bind using the kernel keyring",
            "args": [
                ("pool_name", {"help": "Pool name"}),
                ("keydesc", {"help": "key description"}),
            ],
            "epilog": str(
                MoveNotice("keyring", "pool bind", "pool encryption bind", "3.10.0")
            ),
            "func": BindActions.bind_keyring,
        },
    ),
]

REBIND_SUBCMDS = [
    (
        "clevis",
        {
            "help": (
                "Rebind the specified pool using the current Clevis configuration"
            ),
            "args": [
                ("pool_name", {"help": "Pool name"}),
                (
                    "--token-slot",
                    {
                        "help": (
                            "token slot; may be specified if there is more "
                            "than one binding with the specified method; for "
                            "V2 pools only"
                        ),
                        "type": ensure_nat,
                    },
                ),
            ],
            "epilog": str(
                MoveNotice("clevis", "pool rebind", "pool encryption rebind", "3.10.0")
            ),
            "func": RebindActions.rebind_clevis,
        },
    ),
    (
        "keyring",
        {
            "help": (
                "Rebind the specified pool using the specified key in the "
                "kernel keyring"
            ),
            "args": [
                ("pool_name", {"help": "Pool name"}),
                ("keydesc", {"help": "key description"}),
                (
                    "--token-slot",
                    {
                        "help": (
                            "token slot; may be specified if there is more "
                            "than one binding with the specified method; for "
                            "V2 pools only"
                        ),
                        "type": ensure_nat,
                    },
                ),
            ],
            "epilog": str(
                MoveNotice("keyring", "pool rebind", "pool encryption rebind", "3.10.0")
            ),
            "func": RebindActions.rebind_keyring,
        },
    ),
]

BIND_SUBCMDS_ENCRYPTION = [
    (
        str(Clevis.NBDE),
        {
            "help": "Bind using NBDE via a tang server",
            "args": [
                (
                    "--post-parser",
                    {
                        "action": RejectAction,
                        "default": ClevisEncryptionOptionsForTang,
                        "help": SUPPRESS,
                        "nargs": "?",
                    },
                ),
                ("url", {"help": "URL of tang server"}),
            ],
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": "Choose one option to specify the pool to bind",
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                ),
                (
                    "Tang Server Verification",
                    {
                        "description": "Choose one option",
                        "mut_ex_args": [(True, TRUST_URL_OR_THUMBPRINT)],
                    },
                ),
            ],
            "aliases": [str(Clevis.TANG)],
            "func": BindActions.bind_clevis,
        },
    ),
    (
        str(Clevis.TPM2),
        {
            "help": "Bind using TPM2",
            "args": [
                (
                    "--post-parser",
                    {
                        "action": RejectAction,
                        "default": ClevisEncryptionOptionsForTpm2,
                        "help": SUPPRESS,
                        "nargs": "?",
                    },
                ),
            ],
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": "Choose one option to specify the pool to bind",
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                )
            ],
            "func": BindActions.bind_clevis,
        },
    ),
    (
        "keyring",
        {
            "help": "Bind using the kernel keyring",
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": "Choose one option to specify the pool to bind",
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                )
            ],
            "args": [
                ("keydesc", {"help": "key description"}),
            ],
            "func": BindActions.bind_keyring,
        },
    ),
]

REBIND_SUBCMDS_ENCRYPTION = [
    (
        "clevis",
        {
            "help": (
                "Rebind the specified pool using the current Clevis configuration"
            ),
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": "Choose one option to specify the pool to rebind",
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                )
            ],
            "args": [
                (
                    "--token-slot",
                    {
                        "help": (
                            "token slot; may be specified if there is more "
                            "than one binding with the specified method; for "
                            "V2 pools only"
                        ),
                        "type": ensure_nat,
                    },
                ),
            ],
            "func": RebindActions.rebind_clevis,
        },
    ),
    (
        "keyring",
        {
            "help": (
                "Rebind the specified pool using the specified key in the "
                "kernel keyring"
            ),
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": "Choose one option to specify the pool to rebind",
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                )
            ],
            "args": [
                ("keydesc", {"help": "key description"}),
                (
                    "--token-slot",
                    {
                        "help": (
                            "token slot; may be specified if there is more "
                            "than one binding with the specified method; for "
                            "V2 pools only"
                        ),
                        "type": ensure_nat,
                    },
                ),
            ],
            "func": RebindActions.rebind_keyring,
        },
    ),
]

ENCRYPTION_SUBCMDS = [
    (
        "on",
        {
            "help": "Make encrypted a previously unencrypted pool",
            "args": [
                (
                    "--post-parser",
                    {
                        "action": RejectAction,
                        "default": ClevisEncryptionOptions,
                        "help": SUPPRESS,
                        "nargs": "?",
                    },
                )
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
                (
                    "Encryption",
                    {
                        "description": "Arguments controlling encryption",
                        "args": CLEVIS_AND_KERNEL,
                    },
                ),
                (
                    "Tang Server Verification (only if --tang-url option is set)",
                    {
                        "description": "Choose one option",
                        "mut_ex_args": [(False, TRUST_URL_OR_THUMBPRINT)],
                    },
                ),
            ],
            "func": CryptActions.encrypt,
        },
    ),
    (
        "off",
        {
            "help": "Make unencrypted a previously encrypted pool",
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": "Choose one option to specify the pool",
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                )
            ],
            "func": CryptActions.unencrypt,
        },
    ),
    (
        "reencrypt",
        {
            "help": "Reencrypt an encrypted pool with a new master key",
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": "Choose one option to specify the pool",
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                )
            ],
            "func": CryptActions.reencrypt,
        },
    ),
    (
        "bind",
        {
            "help": "Bind the given pool with an additional encryption facility",
            "subcmds": BIND_SUBCMDS_ENCRYPTION,
        },
    ),
    (
        "rebind",
        {
            "help": (
                "Rebind the given pool with a currently in use encryption "
                "facility but new credentials"
            ),
            "subcmds": REBIND_SUBCMDS_ENCRYPTION,
        },
    ),
    (
        "unbind",
        {
            "help": "Unbind the given pool, removing use of the specified encryption method",
            "groups": [
                (
                    "Pool Identifier",
                    {
                        "description": "Choose one option to specify the pool to unbind",
                        "mut_ex_args": [
                            (True, UUID_OR_NAME),
                        ],
                    },
                )
            ],
            "args": [
                (
                    "method",
                    {
                        "choices": list(EncryptionMethod),
                        "help": "Encryption method to unbind",
                        "type": EncryptionMethod,
                    },
                ),
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
]
