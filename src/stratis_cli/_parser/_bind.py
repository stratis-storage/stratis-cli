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

BIND_SUBCMDS = [
    (
        "nbde",
        dict(
            help="Bind using NBDE via a tang server",
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
                (
                    "key_description",
                    dict(
                        action="store",
                        help="Description of key in kernel keyring used by this pool",
                    ),
                ),
                ("url", dict(action="store", help="URL of tang server")),
                (
                    "--thumbprint",
                    dict(
                        action="store",
                        help="Thumbprint of tang server verification key",
                    ),
                ),
            ],
            aliases=["tang"],
            func=TopActions.bind_tang,
        ),
    ),
    (
        "tpm",
        dict(
            help="Bind using TPM",
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
                (
                    "key_description",
                    dict(
                        action="store",
                        help="Description of key in kernel keyring used by this pool",
                    ),
                ),
            ],
            func=TopActions.bind_tpm,
        ),
    ),
]
