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
    ('create',
     dict(
         help='Create a pool',
         args=[
             ('pool_name', dict(
                 action='store',
                 help='Name of new pool',
             )),
             ('blockdevs',
              dict(
                  help='Create the pool using these block devs',
                  nargs='+',
              )),
             ('--force',
              dict(
                  action='store_true',
                  default=False,
                  help="Overwrite existing metadata on specified devices",
              )),
             ('--redundancy',
              dict(
                  action='store',
                  choices=['none'],
                  default='none',
                  help="Redundancy level for this pool",
              )),
         ],
         func=TopActions.create_pool,
     )),
    ('list',
     dict(
         help="List pools",
         description="Lists Stratis pools that exist on the system",
         func=TopActions.list_pools,
         default=True,
     )),
    ('destroy',
     dict(
         help='Destroy a pool',
         args=[
             ('pool_name', dict(
                 action='store',
                 help='pool name',
             )),
         ],
         func=TopActions.destroy_pool,
     )),
    ('rename',
     dict(
         help='Rename a pool',
         args=[
             ('current', dict(
                 action='store',
                 help='Current pool name',
             )),
             ('new', dict(
                 action='store',
                 help='New pool name',
             )),
         ],
         func=TopActions.rename_pool,
     )),
]
