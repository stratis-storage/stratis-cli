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
Key command parser for Stratis CLI.
"""

from .._actions import TopActions

KEY_SUBCMDS = [
    (
        "set",
        {
            "help": "Set a key in the kernel keyring",
            "args": [("keydesc", {"help": "key description"})],
            "mut_ex_args": [
                (
                    True,
                    [
                        (
                            "--keyfile-path",
                            {
                                "help": (
                                    "Path to the key file containing a key to set "
                                    "in the keyring"
                                ),
                                "dest": "keyfile_path",
                            },
                        ),
                        (
                            "--capture-key",
                            {
                                "action": "store_true",
                                "help": (
                                    "Read key from stdin with no terminal echo or "
                                    "userspace buffer storage"
                                ),
                                "dest": "capture_key",
                            },
                        ),
                    ],
                )
            ],
            "func": TopActions.set_key,
        },
    ),
    (
        "reset",
        {
            "help": "Reset an existing key in the kernel keyring",
            "args": [("keydesc", {"help": "key description"})],
            "mut_ex_args": [
                (
                    True,
                    [
                        (
                            "--keyfile-path",
                            {
                                "help": (
                                    "Path to the key file containing a key to reset "
                                    "in the keyring"
                                ),
                                "dest": "keyfile_path",
                            },
                        ),
                        (
                            "--capture-key",
                            {
                                "action": "store_true",
                                "help": (
                                    "Read key from stdin with no terminal echo or "
                                    "userspace buffer storage"
                                ),
                                "dest": "capture_key",
                            },
                        ),
                    ],
                )
            ],
            "func": TopActions.reset_key,
        },
    ),
    (
        "unset",
        {
            "help": "Unset a key in the kernel keyring",
            "args": [("keydesc", {"help": "key description"})],
            "func": TopActions.unset_key,
        },
    ),
    (
        "list",
        {"help": "List Stratis keys in kernel keyring", "func": TopActions.list_keys},
    ),
]
