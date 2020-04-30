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
        dict(
            help="Set a key in the kernel keyring",
            args=[("keydesc", dict(action="store", help="key description"))],
            mut_ex_args=[
                (
                    True,
                    [
                        (
                            "--keyfile-path",
                            dict(
                                action="store",
                                nargs=1,
                                help=(
                                    "Path to the key file containing a key to set "
                                    "in the keyring"
                                ),
                                dest="keyfile_path",
                            ),
                        ),
                        (
                            "--capture-key",
                            dict(
                                action="store_true",
                                help=(
                                    "Read key from stdin with no terminal echo or "
                                    "userspace buffer storage"
                                ),
                                dest="capture_key",
                            ),
                        ),
                    ],
                )
            ],
            func=TopActions.add_key,
        ),
    ),
    (
        "reset",
        dict(
            help="Reset an existing key in the kernel keyring",
            args=[("keydesc", dict(action="store", help="key description"))],
            mut_ex_args=[
                (
                    True,
                    [
                        (
                            "--keyfile-path",
                            dict(
                                action="store",
                                nargs=1,
                                help=(
                                    "Path to the key file containing a key to reset "
                                    "in the keyring"
                                ),
                                dest="keyfile_path",
                            ),
                        ),
                        (
                            "--capture-key",
                            dict(
                                action="store_true",
                                help=(
                                    "Read key from stdin with no terminal echo or "
                                    "userspace buffer storage"
                                ),
                                dest="capture_key",
                            ),
                        ),
                    ],
                )
            ],
            func=TopActions.update_key,
        ),
    ),
    (
        "unset",
        dict(
            help="Unset a key in the kernel keyring",
            args=[("keydesc", dict(action="store", help="key description"))],
            func=TopActions.remove_key,
        ),
    ),
    (
        "list",
        dict(help="List Stratis keys in kernel keyring", func=TopActions.list_keys),
    ),
]
