# Copyright 2024 Red Hat, Inc.
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
Filesystem listing.
"""

# isort: THIRDPARTY
from dateutil import parser as date_parser
from justbytes import Range

from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import TOTAL_USED_FREE, get_property, print_table, size_triple


def list_filesystems(
    uuid_formatter, *, pool_name=None, fs_id=None
):  # pylint: disable=too-many-locals
    """
    List the specified information about filesystems.
    """
    assert fs_id is None or pool_name is not None

    # pylint: disable=import-outside-toplevel
    from ._data import MOFilesystem, MOPool, ObjectManager, filesystems, pools

    proxy = get_object(TOP_OBJECT)
    managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

    if pool_name is None:
        props = None
        pool_object_path = None
        fs_props = None
        requires_unique = False
    else:
        props = {"Name": pool_name}
        pool_object_path = next(
            pools(props=props).require_unique_match(True).search(managed_objects)
        )[0]
        fs_props = {"Pool": pool_object_path} | (
            {} if fs_id is None else fs_id.managed_objects_key()
        )
        requires_unique = fs_id is not None

    path_to_name = dict(
        (path, MOPool(info).Name())
        for path, info in pools(props=props).search(managed_objects)
    )

    filesystems_with_props = [
        MOFilesystem(info)
        for objpath, info in filesystems(props=fs_props)
        .require_unique_match(requires_unique)
        .search(managed_objects)
    ]

    if fs_id is None:
        klass = List(
            uuid_formatter,
            filesystems_with_props,
            path_to_name,
        )
    else:
        klass = List(
            uuid_formatter,
            filesystems_with_props,
            path_to_name,
        )

    klass.list_filesystems()


class List:  # pylint: disable=too-few-public-methods
    """
    Handle listing a filesystem or filesystems.
    """

    def __init__(self, uuid_formatter, filesystems_with_props, path_to_name):
        """
        Initialize a List object.
        :param uuid_formatter: function to format a UUID str or UUID
        :param uuid_formatter: str or UUID -> str
        :param bool stopped: whether to list stopped pools
        """
        self.uuid_formatter = uuid_formatter
        self.filesystems_with_props = filesystems_with_props
        self.path_to_name = path_to_name

    def list_filesystems(self):
        """
        List the pools.
        """

        def filesystem_size_quartet(dbus_props):
            """
            Calculate the triple to display for filesystem size.

            :param dbus_props: filesystem D-Bus properties
            :type dbus_props: MOFilesystem

            :returns: a string a formatted string showing all three values
            :rtype: str
            """
            total = Range(dbus_props.Size())
            used = get_property(dbus_props.Used(), Range, None)
            limit = get_property(dbus_props.SizeLimit(), Range, None)
            return f'{size_triple(total, used)} / {"None" if limit is None else limit}'

        tables = [
            (
                self.path_to_name[mofilesystem.Pool()],
                mofilesystem.Name(),
                filesystem_size_quartet(mofilesystem),
                date_parser.parse(mofilesystem.Created())
                .astimezone()
                .strftime("%b %d %Y %H:%M"),
                mofilesystem.Devnode(),
                self.uuid_formatter(mofilesystem.Uuid()),
            )
            for mofilesystem in self.filesystems_with_props
        ]

        print_table(
            [
                "Pool",
                "Filesystem",
                f"{TOTAL_USED_FREE} / Limit",
                "Created",
                "Device",
                "UUID",
            ],
            sorted(tables, key=lambda entry: (entry[0], entry[1])),
            ["<", "<", "<", "<", "<", "<"],
        )
