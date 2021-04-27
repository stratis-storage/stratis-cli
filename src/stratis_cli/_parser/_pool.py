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

from .._actions import PoolActions
from .._stratisd_constants import EncryptionMethod
from ._bind import BIND_SUBCMDS

POOL_SUBCMDS = [
    (
        "create",
        dict(
            help="Create a pool",
            args=[
                ("pool_name", dict(action="store", help="Name of new pool")),
                (
                    "blockdevs",
                    dict(help="Create the pool using these block devs", nargs="+"),
                ),
                (
                    "--redundancy",
                    dict(
                        action="store",
                        choices=["none"],
                        default="none",
                        help="Redundancy level for this pool",
                    ),
                ),
                (
                    "--key-desc",
                    dict(
                        default=None,
                        type=str,
                        help=(
                            "Key description of key in kernel keyring to use "
                            "for encryption"
                        ),
                        dest="key_desc",
                    ),
                ),
                (
                    "--clevis",
                    dict(
                        default=None,
                        type=str,
                        help=("Specification for binding with Clevis."),
                        dest="clevis",
                        choices=["nbde", "tang", "tpm2"],
                    ),
                ),
                (
                    "--tang-url",
                    dict(
                        default=None,
                        type=str,
                        help=(
                            "URL of Clevis tang server (ignored if "
                            "--clevis=[tang|nbde] not set)"
                        ),
                        dest="tang_url",
                    ),
                ),
            ],
            mut_ex_args=[
                (
                    False,
                    [
                        (
                            "--trust-url",
                            dict(
                                action="store_true",
                                help=(
                                    "Omit verification of tang server "
                                    "credentials (ignored if "
                                    "--clevis=[tang|nbde] not set)"
                                ),
                                dest="trust_url",
                            ),
                        ),
                        (
                            "--thumbprint",
                            dict(
                                action="store",
                                help=(
                                    "Thumbprint of tang server at specified "
                                    "URL (ignored if --clevis=[tang|nbde] not "
                                    "set)"
                                ),
                                dest="thumbprint",
                            ),
                        ),
                    ],
                )
            ],
            func=PoolActions.create_pool,
        ),
    ),
    (
        "init-cache",
        dict(
            help="Initialize the cache with block devices",
            args=[
                (
                    "pool_name",
                    dict(
                        action="store",
                        help=("Name of the pool for which to initialize the cache"),
                    ),
                ),
                (
                    "blockdevs",
                    dict(
                        help="Initialize the pool cache using these block devs",
                        nargs="+",
                    ),
                ),
            ],
            func=PoolActions.init_cache,
        ),
    ),
    (
        "list",
        dict(
            help="List pools",
            description="Lists Stratis pools that exist on the system",
            func=PoolActions.list_pools,
        ),
    ),
    (
        "destroy",
        dict(
            help="Destroy a pool",
            args=[("pool_name", dict(action="store", help="pool name"))],
            func=PoolActions.destroy_pool,
        ),
    ),
    (
        "rename",
        dict(
            help="Rename a pool",
            args=[
                ("current", dict(action="store", help="Current pool name")),
                ("new", dict(action="store", help="New pool name")),
            ],
            func=PoolActions.rename_pool,
        ),
    ),
    (
        "add-data",
        dict(
            help="Add one or more blockdevs to an existing pool for use as data storage",
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
                (
                    "blockdevs",
                    dict(
                        help="Block devices to add to the pool",
                        metavar="blockdev",
                        nargs="+",
                    ),
                ),
            ],
            func=PoolActions.add_data_devices,
        ),
    ),
    (
        "add-cache",
        dict(
            help="Add one or more blockdevs to an existing pool for use as cache",
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
                (
                    "blockdevs",
                    dict(
                        help="Block devices to add to the pool as cache",
                        metavar="blockdev",
                        nargs="+",
                    ),
                ),
            ],
            func=PoolActions.add_cache_devices,
        ),
    ),
    (
        "bind",
        dict(
            help="Bind the given pool with an additional encryption facility",
            subcmds=BIND_SUBCMDS,
        ),
    ),
    (
        "unbind",
        dict(
            help="Unbind the given pool, removing support for encryption with Clevis",
            args=[
                (
                    "method",
                    dict(
                        action="store",
                        choices=[str(x) for x in list(EncryptionMethod)],
                        help="Encryption method to unbind",
                    ),
                ),
                ("pool_name", dict(action="store", help="Pool name")),
            ],
            func=PoolActions.unbind,
        ),
    ),
    (
        "unlock",
        dict(
            help="Unlock all of the currently locked encrypted pools",
            args=[
                (
                    "unlock_method",
                    dict(
                        default=str(EncryptionMethod.KEYRING),
                        action="store",
                        choices=[str(x) for x in list(EncryptionMethod)],
                        help="Method to use to unlock encrypted pools",
                    ),
                )
            ],
            func=PoolActions.unlock_pools,
        ),
    ),
]
