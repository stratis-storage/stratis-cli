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

from .._actions import TopActions

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
            ],
            func=TopActions.create_pool,
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
            func=TopActions.init_cache,
        ),
    ),
    (
        "list",
        dict(
            help="List pools",
            description="Lists Stratis pools that exist on the system",
            func=TopActions.list_pools,
        ),
    ),
    (
        "destroy",
        dict(
            help="Destroy a pool",
            args=[("pool_name", dict(action="store", help="pool name"))],
            func=TopActions.destroy_pool,
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
            func=TopActions.rename_pool,
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
            func=TopActions.add_data_devices,
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
            func=TopActions.add_cache_devices,
        ),
    ),
    (
        "unlock",
        dict(
            help="Unlock all of the currently locked encrypted pools",
            func=TopActions.unlock_pools,
        ),
    ),
]
