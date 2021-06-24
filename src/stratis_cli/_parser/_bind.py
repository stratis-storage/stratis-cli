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
Bind/Rebind command parser for Stratis CLI.
"""

from .._actions import BindActions, RebindActions

BIND_SUBCMDS = [
    (
        "nbde",
        dict(
            help="Bind using NBDE via a tang server",
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
                ("url", dict(action="store", help="URL of tang server")),
            ],
            mut_ex_args=[
                (
                    True,
                    [
                        (
                            "--trust-url",
                            dict(
                                action="store_true",
                                help="Omit verification of tang server credentials",
                                dest="trust_url",
                            ),
                        ),
                        (
                            "--thumbprint",
                            dict(
                                action="store",
                                help="Thumbprint of tang server at specified URL",
                                dest="thumbprint",
                            ),
                        ),
                    ],
                )
            ],
            aliases=["tang"],
            func=BindActions.bind_tang,
        ),
    ),
    (
        "tpm2",
        dict(
            help="Bind using TPM2",
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
            ],
            func=BindActions.bind_tpm,
        ),
    ),
    (
        "keyring",
        dict(
            help="Bind using the kernel keyring",
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
                ("keydesc", dict(action="store", help="key description")),
            ],
            func=BindActions.bind_keyring,
        ),
    ),
]

REBIND_SUBCMDS = [
    (
        "clevis",
        dict(
            help="Rebind using current Clevis nbde/tang configuration",
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
            ],
            func=RebindActions.rebind_clevis,
        ),
    ),
    (
        "keyring",
        dict(
            help="Rebind with a key specified in the kernel keyring",
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
                ("keydesc", dict(action="store", help="key description")),
            ],
            func=RebindActions.rebind_keyring,
        ),
    ),
]
