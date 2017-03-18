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
Definition of cache actions to display in the CLI.
"""


from .._actions import CacheActions

CACHE_SUBCMDS = [
    ('add',
     dict(
         help="Add one or more blockdevs to a pool as cache devices",
         args=[
             ('pool_name',
              dict(
                  action='store',
                  help='Pool name',
              )),
             ('device',
              dict(
                  help='Block devices to add to the pool cache tier',
                  metavar='blockdev',
                  nargs='+',
              )),
             ('--force',
              dict(
                  action='store_true',
                  default=False,
                  help="Use devices even if they appear to contain existing data",
              )),
         ],
         func=CacheActions.add_devices,
     )),
    ('remove',
     dict(
         help="Remove one or more caching blockdevs from an existing pool",
         args=[
             ('pool_name',
              dict(
                  action='store',
                  help='Pool name'
              )),
             ('device',
              dict(
                  help='Block devices to remove from the pool cache tier',
                  metavar='blockdev',
                  nargs='+',
              )),
         ],
         func=CacheActions.remove_device,
     )),
    ('list',
     dict(
         help="List information about cache devices in the pool",
         args=[
             ('pool_name',
              dict(
                  action='store',
                  help='Pool name',
              )),
         ],
         func=CacheActions.list_cache,
     )),
]
