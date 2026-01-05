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
from typing import Any, Callable, Dict, List, Optional

# isort: THIRDPARTY
from dateutil import parser as date_parser
from dbus import ObjectPath, String
from justbytes import Range

from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import (
    TABLE_FAILURE_STRING,
    TABLE_UNKNOWN_STRING,
    TOTAL_USED_FREE,
    catch_missing_property,
    get_property,
    print_table,
)
from ._utils import SizeTriple


def list_filesystems(
    uuid_formatter: Callable, *, pool_name=None, fs_id=None
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
            uuid_formatter,
            filesystems_with_props,
            pool_object_path_to_pool_name,
        )
    else:
        klass = Detail(
            uuid_formatter,
            filesystems_with_props,
            pool_object_path_to_pool_name,
        )

    klass.display()


class ListFilesystem(ABC):  # pylint: disable=too-few-public-methods
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
        return SizeTriple(
            catch_missing_property(lambda mo: Range(mo.Size()), None)(mofs),
            catch_missing_property(
                lambda mo: get_property(mo.Used(), Range, None), None
            )(mofs),
        )


class Table(ListFilesystem):  # pylint: disable=too-few-public-methods
    """
    List filesystems using table format.
    """

    def display(self):
        """
        List the filesystems.
        """

        def filesystem_size_quartet(
            size_triple: SizeTriple, limit: Optional[Range]
        ) -> str:
            """
            Calculate the triple to display for filesystem size.

            :returns: a string a formatted string showing all three values
            :rtype: str
            """
            triple_str = " / ".join(
                (
                    TABLE_FAILURE_STRING if x is None else str(x)
                    for x in (
                        size_triple.total(),
                        size_triple.used(),
                        size_triple.free(),
                    )
                )
            )
            return f"{triple_str} / {limit}"

        def missing_property(func: Callable[[Any], str]) -> Callable[[Any], str]:
            return catch_missing_property(func, TABLE_UNKNOWN_STRING)

        pool_name_func = missing_property(
            lambda mo: self.pool_object_path_to_pool_name.get(
                mo.Pool(), TABLE_UNKNOWN_STRING
            )
        )
        name_func = missing_property(lambda mofs: mofs.Name())
        size_func = missing_property(
            lambda mofs: filesystem_size_quartet(
                ListFilesystem.size_triple(mofs),
                get_property(mofs.SizeLimit(), Range, None),
            )
        )
        devnode_func = missing_property(lambda mofs: mofs.Devnode())
        uuid_func = missing_property(lambda mofs: self.uuid_formatter(mofs.Uuid()))

        tables = [
            (
                pool_name_func(mofilesystem),
                name_func(mofilesystem),
                size_func(mofilesystem),
                devnode_func(mofilesystem),
                uuid_func(mofilesystem),
            )
            for mofilesystem in self.filesystems_with_props
        ]

        print_table(
            [
                "Pool",
                "Filesystem",
                f"{TOTAL_USED_FREE} / Limit",
                "Device",
                "UUID",
            ],
            sorted(tables, key=lambda entry: (entry[0], entry[1])),
            ["<", "<", "<", "<", "<"],
        )


class Detail(ListFilesystem):  # pylint: disable=too-few-public-methods
    """
    Do a detailed listing of filesystems.
    """

    def display(self):
        """
        List the filesystems.
        """
        assert len(self.filesystems_with_props) == 1

        fs = self.filesystems_with_props[0]

        def missing_property(func: Callable[[Any], str]) -> Callable[[Any], str]:
            return catch_missing_property(func, TABLE_UNKNOWN_STRING)(fs)

        uuid = missing_property(lambda mo: self.uuid_formatter(mo.Uuid()))
        print(f"UUID: {uuid}")

        name = missing_property(lambda mo: mo.Name())
        print(f"Name: {name}")

        pool = missing_property(
            lambda mo: self.pool_object_path_to_pool_name.get(
                mo.Pool(), TABLE_UNKNOWN_STRING
            ),
        )
        print(f"Pool: {pool}")

        devnode = missing_property(lambda mo: mo.Devnode())
        print()
        print(f"Device: {devnode}")

        created = missing_property(
            lambda mo: date_parser.isoparse(mo.Created())
            .astimezone()
            .strftime("%b %d %Y %H:%M"),
        )
        print()
        print(f"Created: {created}")

        origin = catch_missing_property(
            lambda mo: get_property(mo.Origin(), self.uuid_formatter, None), None
        )
        print()
        print(f"Snapshot origin: {origin}")
        if origin is not None:
            scheduled = missing_property(
                lambda mo: "Yes" if mo.MergeScheduled() else "No"
            )
            print(f"    Revert scheduled: {scheduled}")

        size_triple = ListFilesystem.size_triple(fs)
        print()
        print("Sizes:")
        print(
            "  Logical size of thin device: "
            f"{TABLE_FAILURE_STRING if size_triple.total() is None else size_triple.total()}"
        )
        print(
            "  Total used (including XFS metadata): "
            f"{TABLE_FAILURE_STRING if size_triple.used() is None else size_triple.used()}"
        )
        print(
            "  Free: "
            f"{TABLE_FAILURE_STRING if size_triple.free() is None else size_triple.free()}"
        )

        limit = missing_property(
            lambda mo: get_property(mo.SizeLimit(), lambda x: str(Range(x)), str(None))
        )
        print()
        print(f"  Size Limit: {limit}")
