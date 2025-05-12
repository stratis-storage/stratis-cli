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
from argparse import SUPPRESS

from .._actions import BindActions, RebindActions
from .._constants import Clevis
from ._shared import (
    TRUST_URL_OR_THUMBPRINT,
    ClevisEncryptionOptions,
    RejectAction,
    ensure_nat,
)


class ClevisEncryptionOptionsForTang(
    ClevisEncryptionOptions
):  # pylint: disable=too-few-public-methods
    """
    Class that verifies Clevis encryption options for bind subcommand.
    """

    def __init__(self, namespace):
        namespace.clevis = Clevis.TANG
        namespace.tang_url = copy.copy(namespace.url)
        del namespace.url
        super().__init__(namespace)


class ClevisEncryptionOptionsForTpm2(
    ClevisEncryptionOptions
):  # pylint: disable=too-few-public-methods
    """
    Class that verifies Clevis encryption options for bind subcommand.
    """

    def __init__(self, namespace):
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
            "func": RebindActions.rebind_keyring,
        },
    ),
]
