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
from .._constants import YesOrNo
from .._error_codes import PoolErrorCode
from .._stratisd_constants import EncryptionMethod
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
        dict(
            help="Create a pool",
            args=[
                ("pool_name", dict(action="store", help="Name of new pool")),
                (
                    "blockdevs",
                    dict(help="Create the pool using these block devs", nargs="+"),
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
                (
                    "--no-overprovision",
                    dict(
                        action="store_true",
                        help=(
                            "Do not allow the sum of the logical size of the "
                            "pool's filesystems to exceed the size of the "
                            "pool's data area."
                        ),
                        dest="no_overprovision",
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
        "stop",
        dict(
            help=(
                "Stop a pool. Tear down the pool's storage stack "
                "but do not erase any metadata."
            ),
            args=[
                (
                    "pool_name",
                    dict(
                        action="store",
                        help="Name of the pool to stop",
                    ),
                )
            ],
            func=PoolActions.stop_pool,
        ),
    ),
    (
        "start",
        dict(
            help="Start a pool.",
            mut_ex_args=[
                (
                    True,
                    [
                        (
                            "--uuid",
                            dict(
                                action="store",
                                type=UUID,
                                help="UUID of the pool to start",
                            ),
                        ),
                        (
                            "--name",
                            dict(action="store", help="name of the pool to start"),
                        ),
                    ],
                )
            ],
            args=[
                (
                    "--unlock-method",
                    dict(
                        default=None,
                        dest="unlock_method",
                        action="store",
                        choices=[str(x) for x in list(EncryptionMethod)],
                        help="Method to use to unlock the pool if encrypted.",
                    ),
                ),
            ],
            func=PoolActions.start_pool,
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
            description="List Stratis pools",
            mut_ex_args=[
                (
                    False,
                    [
                        (
                            "--uuid",
                            dict(
                                action="store",
                                type=UUID,
                                help="UUID of pool to list",
                            ),
                        ),
                        (
                            "--name",
                            dict(
                                action="store",
                                help="name of pool to list",
                            ),
                        ),
                    ],
                ),
            ],
            args=[
                (
                    "--stopped",
                    dict(
                        action="store_true",
                        help="Display information about stopped pools only.",
                    ),
                ),
            ],
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
        "extend-data",
        dict(
            help=(
                "Extend the pool's data capacity with additional storage "
                "space offered by its component data devices through, e.g., "
                "expansion of a component RAID device."
            ),
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
                (
                    "--device-uuid",
                    dict(
                        action="extend",
                        dest="device_uuid",
                        nargs="*",
                        type=UUID,
                        default=[],
                        help=(
                            "UUID of device to use; may be specified multiple "
                            "times. If no devices are specified then all "
                            "devices belonging to the pool that appear to have "
                            "increased in size will be used."
                        ),
                    ),
                ),
            ],
            func=PoolActions.extend_data,
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
        "rebind",
        dict(
            help=(
                "Rebind the given pool with a currently in use encryption "
                "facility but new credentials"
            ),
            subcmds=REBIND_SUBCMDS,
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
            func=BindActions.unbind,
        ),
    ),
    (
        "set-fs-limit",
        dict(
            help="Set the maximum number of filesystems the pool can support.",
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
                (
                    "amount",
                    dict(
                        action="store", type=_ensure_nat, help="Number of filesystems."
                    ),
                ),
            ],
            func=PoolActions.set_fs_limit,
        ),
    ),
    (
        "overprovision",
        dict(
            help="Specify whether or not to allow overprovisioning for the pool.",
            args=[
                ("pool_name", dict(action="store", help="Pool name")),
                (
                    "decision",
                    dict(
                        action="store",
                        help="yes to allow overprovisioning, otherwise no",
                        choices=[str(x) for x in list(YesOrNo)],
                    ),
                ),
            ],
            func=PoolActions.set_overprovisioning_mode,
        ),
    ),
    (
        "explain",
        dict(
            help="Explain pool alert codes",
            args=[
                (
                    "code",
                    dict(
                        action="store",
                        choices=[str(x) for x in PoolErrorCode.codes()],
                        help="Error code to explain",
                    ),
                )
            ],
            func=PoolActions.explain_code,
        ),
    ),
    (
        "debug",
        dict(
            help=("Miscellaneous pool-level debug commands"),
            subcmds=POOL_DEBUG_SUBCMDS,
        ),
    ),
]
