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
import glob
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import UUID

# isort: THIRDPARTY
from dateutil import parser as date_parser
from dbus import ObjectPath, String
from justbytes import Range

from .._constants import FilesystemId, IdType
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import (
    TABLE_FAILURE_STRING,
    TOTAL_USED_FREE,
    get_property,
    print_table,
)
from ._utils import SizeTriple


def _read_filesystem_symlinks(
    *, pool_name: Optional[str] = None, fs_name: Optional[str] = None
) -> defaultdict[str, set[str]]:
    """
    Return a dict of pool names to filesystem names based on reading the
    directory of filesystem links at /dev/stratis.

    Restrict to just one pool if pool_name is specified.
    """
    pools_and_fss = defaultdict(set)
    for path in glob.glob(
        os.path.join(
            "/",
            *(
                ["dev", "stratis"]
                + (["*"] if pool_name is None else [pool_name])
                + (["*"] if fs_name is None else [fs_name])
            ),
        )
    ):
        p_path = Path(path)
        pools_and_fss[p_path.parent.name].add(p_path.name)
    return pools_and_fss


def list_filesystems(
    uuid_formatter: Callable,
    *,
    pool_name: Optional[str] = None,
    fs_id: Optional[FilesystemId] = None,
    use_dev_dir: bool = False,
):  # pylint: disable=too-many-locals
    """
    List the specified information about filesystems.
    """
    assert fs_id is None or pool_name is not None

    # pylint: disable=import-outside-toplevel
    from ._data import MOFilesystem, MOPool, ObjectManager, filesystems, pools

    pools_and_fss = (
        _read_filesystem_symlinks(
            pool_name=pool_name,
            fs_name=(  # pyright: ignore [ reportArgumentType ]
                fs_id.id_value
                if fs_id is not None and fs_id.id_type is IdType.NAME
                else None
            ),
        )
        if use_dev_dir
        else None
    )

    proxy = get_object(TOP_OBJECT)
    managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

    if pool_name is None:
        props = None
        pool_object_path = None
        fs_props = None
    else:
        props = {"Name": pool_name}
        pool_object_path = next(
            pools(props=props).require_unique_match(True).search(managed_objects)
        )[0]
        fs_props = {"Pool": pool_object_path} | (
            {} if fs_id is None else fs_id.managed_objects_key()
        )

    pool_object_path_to_pool_name = dict(
        (path, MOPool(info).Name())
        for path, info in pools(props=props).search(managed_objects)
    )

    filesystems_with_props = [
        MOFilesystem(info)
        for objpath, info in filesystems(props=fs_props)
        .require_unique_match(
            (not use_dev_dir) and pool_name is not None and fs_id is not None
        )
        .search(managed_objects)
    ]

    klass = ListFilesystem(uuid_formatter)

    if fs_id is None:
        klass.display_table(
            filesystems_with_props,
            pool_object_path_to_pool_name,
            system_pools_and_fss=pools_and_fss,
        )
    else:
        assert (
            pool_name is not None
            and pool_name == pool_object_path_to_pool_name[pool_object_path]
        )
        klass.display_detail(
            pool_name,
            fs_id,
            filesystems_with_props,
            system_pools_and_fss=pools_and_fss,
        )


class ListFilesystem:
    """
    Handle listing a filesystem or filesystems.
    """

    def __init__(self, uuid_formatter: Callable[[Union[str, UUID]], str]):
        """
        Initialize a List object.
        :param uuid_formatter: function to format a UUID str or UUID
        :param uuid_formatter: str or UUID -> str
        """
        self.uuid_formatter = uuid_formatter

    def display_table(
        self,
        filesystems_with_props: List[Any],
        pool_object_path_to_pool_name: Dict[ObjectPath, String],
        *,
        system_pools_and_fss: Optional[defaultdict[str, set[str]]] = None,
    ):
        """
        Display filesystems as a table.
        """

        def filesystem_size_quartet(
            total: Range, used: Optional[Range], limit: Optional[Range]
        ) -> str:
            """
            Calculate the triple to display for filesystem size.

            :returns: a string a formatted string showing all three values
            :rtype: str
            """
            size_triple = SizeTriple(total, used)
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
            return f'{triple_str} / {"None" if limit is None else limit}'

        if system_pools_and_fss is not None:
            tables = []
            for mofilesystem in filesystems_with_props:
                pool_name = pool_object_path_to_pool_name[mofilesystem.Pool()]
                fs_name = mofilesystem.Name()
                if fs_name in system_pools_and_fss.get(pool_name, []):
                    tables.append(
                        (
                            pool_name,
                            fs_name,
                            filesystem_size_quartet(
                                Range(mofilesystem.Size()),
                                get_property(mofilesystem.Used(), Range, None),
                                get_property(mofilesystem.SizeLimit(), Range, None),
                            ),
                            mofilesystem.Devnode(),
                            self.uuid_formatter(mofilesystem.Uuid()),
                        )
                    )
                    system_pools_and_fss[pool_name].remove(fs_name)
            for pool, fss in system_pools_and_fss:
                for fs in fss:
                    tables.append(
                        (
                            pool,
                            fs,
                            "<UNAVAILABLE> / <UNAVAILABLE> / <UNAVAILABLE> / <UNAVAILABLE>",
                            os.path.join("/", "dev", "stratis", pool, fs),
                            "<UNAVAILABLE>",
                        )
                    )
        else:
            tables = [
                (
                    pool_object_path_to_pool_name[mofilesystem.Pool()],
                    mofilesystem.Name(),
                    filesystem_size_quartet(
                        Range(mofilesystem.Size()),
                        get_property(mofilesystem.Used(), Range, None),
                        get_property(mofilesystem.SizeLimit(), Range, None),
                    ),
                    mofilesystem.Devnode(),
                    self.uuid_formatter(mofilesystem.Uuid()),
                )
                for mofilesystem in filesystems_with_props
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

    def display_detail(  # pylint: disable=too-many-locals, too-many-statements
        self,
        pool_name: str,
        fs_id: FilesystemId,
        filesystems_with_props: list[Any],
        *,
        system_pools_and_fss: Optional[defaultdict[str, set[str]]] = None,
    ):
        """
        List the filesystem.
        """

        if len(filesystems_with_props) > 1:
            raise RuntimeError("placeholder")

        fs = None
        fs_name = None
        if len(filesystems_with_props) == 1:
            fs = filesystems_with_props[0]
            fs_name = fs.Name()

            if system_pools_and_fss is not None:
                if fs_name not in system_pools_and_fss.get(pool_name, []):
                    raise RuntimeError("place holder")
        else:
            if system_pools_and_fss is None:
                raise RuntimeError("placeholder")

            if fs_id.id_type is IdType.NAME:
                fs_name = fs_id.id_value
            else:
                raise RuntimeError("placeholder")

        assert fs_name is not None

        if fs is not None:
            size_triple = SizeTriple(
                Range(fs.Size()), get_property(fs.Used(), Range, None)
            )

            limit = get_property(fs.SizeLimit(), Range, None)
            limit_str = "None" if limit is None else limit

            created = (
                date_parser.isoparse(fs.Created())
                .astimezone()
                .strftime("%b %d %Y %H:%M")
            )

            origin = get_property(fs.Origin(), self.uuid_formatter, None)
            origin_str = "None" if origin is None else origin

            uuid = self.uuid_formatter(fs.Uuid())
            pool = pool_name
            devnode = fs.Devnode()

            print(f"UUID: {uuid}")
            print(f"Name: {fs_name}")
            print(f"Pool: {pool}")
            print()
            print(f"Device: {devnode}")
            print()
            print(f"Created: {created}")
            print()
            print(f"Snapshot origin: {origin_str}")
            if origin is not None:
                scheduled = "Yes" if fs.MergeScheduled() else "No"
                print(f"    Revert scheduled: {scheduled}")
            print()
            print("Sizes:")
            print(f"  Logical size of thin device: {size_triple.total()}")
            print(
                "  Total used (including XFS metadata): "
                f"{TABLE_FAILURE_STRING if size_triple.used() is None else size_triple.used()}"
            )
            print(
                "  Free: "
                f"{TABLE_FAILURE_STRING if size_triple.free() is None else size_triple.free()}"
            )
            print()
            print(f"  Size Limit: {limit_str}")
        else:
            print(f"Name: {fs_name}")
            print(f"Pool: {pool_name}")
