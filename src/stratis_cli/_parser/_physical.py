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
Definition of block device actions to display in the CLI.
"""

from .._actions import BlockdevActions

PHYSICAL_SUBCMDS = [
    ('add',
     dict(
         help="Add one or more blockdevs to an existing pool",
         args=[
             ('pool_name',
              dict(
                  action='store',
                  help='Pool name',
              )),
             ('device',
              dict(
                  help='Block devices to add to the pool',
                  metavar='blockdev',
                  nargs='+'
              )),
             ('--force',
              dict(
                  action='store_true',
                  default=False,
                  help="Use devices even if they appear to contain existing data"
              )),
         ],
         func=BlockdevActions.add_device
     )),
    ('list',
     dict(
         help="List information about blockdevs in the pool",
         args=[
             ('pool_name',
              dict(
                  action='store',
                  help='Pool name'
              )),
         ],
         func=BlockdevActions.list_pool
     )),
]
