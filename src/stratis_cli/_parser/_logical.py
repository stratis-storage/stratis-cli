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
Definition of filesystem actions to display in the CLI.
"""

from .._actions import LogicalActions

LOGICAL_SUBCMDS = [
    ('create',
     dict(
         help='Create filesystems in a pool',
         args=[
             ('pool_name',
              dict(
                  action='store',
                  help='pool name',
              )),
             ('fs_name',
              dict(
                  help='Create filesystems in this pool using the given names',
                  nargs='+',
              )),
         ],
         func=LogicalActions.create_volumes
     )),
     ('snapshot',
     dict(
         help='Snapshot the named filesystem in a pool',
         args=[
             ('pool_name',
              dict(
                  action='store',
                  help='pool name',
              )),
             ('origin_name',
              dict(
                  action='store',
                  help='origin name',
              )),
             ('snapshot_name',
              dict(
                  action='store',
                  help='snapshot name',
              )),
         ],
         func=LogicalActions.snapshot_filesystem
     )),
    ('list',
     dict(
         help="List filesystems",
         args=[
             ('pool_name',
              dict(
                  action='store',
                  help='Pool name'
              )),
         ],
         func=LogicalActions.list_volumes
     )),
    ('destroy',
     dict(
         help='Destroy filesystems in a pool',
         args=[
             ('pool_name',
              dict(
                  action='store',
                  help='pool name',
              )),
             ('fs_name',
              dict(
                  help='Destroy the named filesystems in this pool',
                  nargs='+',
              )),
         ],
         func=LogicalActions.destroy_volumes
     )),
    ('rename',
     dict(
         help='Rename a filesystem',
         args=[
             ('pool_name',
              dict(
                  action='store',
                  help='Name of the pool the filesystem is part of',
              )),
             ('fs_name',
              dict(
                  action='store',
                  help='Name of the filesystem to change',
              )),
             ('new_name',
              dict(
                  action='store',
                  help='New name to give that filesystem',
              )),
         ],
         func=LogicalActions.rename_fs,
     )),

]
