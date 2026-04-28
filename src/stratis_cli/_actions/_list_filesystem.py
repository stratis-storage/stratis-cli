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

# isort: STDLIB
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

# isort: THIRDPARTY
from dateutil import parser as date_parser
from dbus import ObjectPath, String
from justbytes import Range

# isort: FIRSTPARTY
from dbus_client_gen import DbusClientMissingPropertyError

from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import (
    TABLE_UNKNOWN_STRING,
    TOTAL_USED_FREE,
    get_property,
    print_table,
)
from ._utils import SizeTriple


def list_filesystems(uuid_formatter: Callable, *, pool_name=None, fs_id=None):
    """
    List the specified information about filesystems.
    """
    assert fs_id is None or pool_name is not None

    from ._data import (  # noqa: PLC0415
        MOFilesystem,
        MOPool,
        ObjectManager,
        filesystems,
        pools,
    )

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

    pool_object_path_to_pool_name = dict(
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
        klass = Table(
            uuid_formatter, filesystems_with_props, pool_object_path_to_pool_name
        )
    else:
        klass = Detail(
            uuid_formatter, filesystems_with_props, pool_object_path_to_pool_name
        )

    klass.display()


class ListFilesystem(ABC):
    """
    Handle listing a filesystem or filesystems.
    """

    def __init__(
        self,
        uuid_formatter: Callable,
        filesystems_with_props: List[Any],
        pool_object_path_to_pool_name: Dict[ObjectPath, String],
    ):
        """
        Initialize a List object.
        :param uuid_formatter: function to format a UUID str or UUID
        :param uuid_formatter: str or UUID -> str
        :param bool stopped: whether to list stopped pools
        """
        self.uuid_formatter = uuid_formatter
        self.filesystems_with_props = filesystems_with_props
        self.pool_object_path_to_pool_name = pool_object_path_to_pool_name

    @abstractmethod
    def display(self):
        """
        List filesystems.
        """

    @staticmethod
    def size_triple(mofs: Any) -> SizeTriple:
        """
        Calculate size triple
        """
        try:
            size = Range(mofs.Size())
        except DbusClientMissingPropertyError:
            size = None

        try:
            used = get_property(mofs.Used(), Range, None)
        except DbusClientMissingPropertyError:
            used = None

        return SizeTriple(size, used)

    @staticmethod
    def limit_str(mofs: Any) -> str:
        """
        Return limit representation for printing.
        """
        try:
            return str(get_property(mofs.SizeLimit(), Range, None))
        except DbusClientMissingPropertyError:
            return TABLE_UNKNOWN_STRING

    @staticmethod
    def devnode_str(mofs: Any) -> str:
        """
        Return devnode representation for printing.
        """
        try:
            return mofs.Devnode()
        except DbusClientMissingPropertyError:
            return TABLE_UNKNOWN_STRING

    @staticmethod
    def name_str(mofs: Any) -> str:
        """
        Return name representation for printing.
        """
        try:
            return mofs.Name()
        except DbusClientMissingPropertyError:  # pragma: no cover
            return TABLE_UNKNOWN_STRING

    def uuid_str(self, mofs: Any) -> str:
        """
        Return representation of UUID, correctly formatted according to options.
        """
        try:
            return self.uuid_formatter(mofs.Uuid())
        except DbusClientMissingPropertyError:  # pragma: no cover
            return TABLE_UNKNOWN_STRING

    def pool_name_str(self, mofs: Any) -> str:
        """
        Return the name of this filesystem's pool.
        """
        try:
            return self.pool_object_path_to_pool_name.get(
                mofs.Pool(), TABLE_UNKNOWN_STRING
            )
        except DbusClientMissingPropertyError:  # pragma: no cover
            return TABLE_UNKNOWN_STRING


class Table(ListFilesystem):
    """
    List filesystems using table format.
    """

    def display(self):
        """
        List the filesystems.
        """

        def filesystem_size_quartet(mofs: Any) -> str:
            """
            Calculate the string to display for filesystem sizes.

            :returns: a properly formatted string
            :rtype: str
            """
            size_triple = ListFilesystem.size_triple(mofs)
            limit = ListFilesystem.limit_str(mofs)

            triple_str = " / ".join(
                (
                    TABLE_UNKNOWN_STRING if x is None else str(x)
                    for x in (
                        size_triple.total(),
                        size_triple.used(),
                        size_triple.free(),
                    )
                )
            )
            return f"{triple_str} / {limit}"

        tables = [
            (
                self.pool_name_str(mofilesystem),
                ListFilesystem.name_str(mofilesystem),
                filesystem_size_quartet(mofilesystem),
                ListFilesystem.devnode_str(mofilesystem),
                self.uuid_str(mofilesystem),
            )
            for mofilesystem in self.filesystems_with_props
        ]

        print_table(
            ["Pool", "Filesystem", f"{TOTAL_USED_FREE} / Limit", "Device", "UUID"],
            sorted(tables, key=lambda entry: (entry[0], entry[1])),
            ["<", "<", "<", "<", "<"],
        )


class Detail(ListFilesystem):
    """
    Do a detailed listing of filesystems.
    """

    def display(self):
        """
        List the filesystems.
        """
        assert len(self.filesystems_with_props) == 1

        fs = self.filesystems_with_props[0]

        print(f"UUID: {self.uuid_str(fs)}")
        print(f"Name: {ListFilesystem.name_str(fs)}")
        print(f"Pool: {self.pool_name_str(fs)}")

        print()
        print(f"Device: {ListFilesystem.devnode_str(fs)}")

        try:
            created = (
                date_parser.isoparse(fs.Created())
                .astimezone()
                .strftime("%b %d %Y %H:%M")
            )
        except DbusClientMissingPropertyError:
            created = TABLE_UNKNOWN_STRING
        print()
        print(f"Created: {created}")

        print()
        try:
            origin = get_property(fs.Origin(), self.uuid_formatter, None)
            print(f"Snapshot origin: {origin}")
            if origin is not None:
                try:
                    scheduled = "Yes" if fs.MergeScheduled() else "No"
                except DbusClientMissingPropertyError:
                    scheduled = TABLE_UNKNOWN_STRING
                print(f"    Revert scheduled: {scheduled}")
        except DbusClientMissingPropertyError:
            print(f"Snapshot origin: {TABLE_UNKNOWN_STRING}")

        def size_str(value: Range | None) -> str:
            return TABLE_UNKNOWN_STRING if value is None else str(value)

        size_triple = ListFilesystem.size_triple(fs)
        print()
        print("Sizes:")
        print(f"  Logical size of thin device: {size_str(size_triple.total())}")
        print(f"  Total used (including XFS metadata): {size_str(size_triple.used())}")
        print(f"  Free: {size_str(size_triple.free())}")

        limit = ListFilesystem.limit_str(fs)
        print()
        print(f"  Size Limit: {limit}")
