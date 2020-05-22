# Copyright 2019 Red Hat, Inc.
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
DBus methods for blackbox testing.
"""
# isort: STDLIB
import os

# isort: THIRDPARTY
import dbus

from .utils import TEST_PREF, umount_mdv


# This function is an exact copy of the get_timeout function in
# the stratis_cli source code, except that it raises RuntimeError where
# that function raises StratisCliEnvironmentError.
# The function should not be imported, as these tests are intended to be
# run in an environment where the Stratis CLI source code is not certainly
# available.
def _get_timeout(value):
    """
    Turn an input str or int into a float timeout value.

    :param value: the input str or int
    :type value: str or int
    :raises RuntimeError:
    :returns: float
    """

    maximum_dbus_timeout_ms = 1073741823

    # Ensure the input str is not a float
    if isinstance(value, float):
        raise RuntimeError(
            "The timeout value provided is a float; it should be an integer."
        )

    try:
        timeout_int = int(value)

    except ValueError:
        raise RuntimeError("The timeout value provided is not an integer.")

    # Ensure the integer is not too small
    if timeout_int < -1:
        raise RuntimeError(
            "The timeout value provided is smaller than the smallest acceptable value, -1."
        )

    # Ensure the integer is not too large
    if timeout_int > maximum_dbus_timeout_ms:
        raise RuntimeError(
            "The timeout value provided exceeds the largest acceptable value, %s."
            % maximum_dbus_timeout_ms
        )

    # Convert from milliseconds to seconds
    return timeout_int / 1000


class StratisDbus:
    "Wrappers around stratisd DBus calls"

    _OBJECT_MANAGER = "org.freedesktop.DBus.ObjectManager"
    _BUS = dbus.SystemBus()
    _BUS_NAME = "org.storage.stratis2"
    _TOP_OBJECT = "/org/storage/stratis2"

    _MNGR_IFACE = "org.storage.stratis2.Manager.r1"
    _REPORT_IFACE = "org.storage.stratis2.Report.r1"
    _POOL_IFACE = "org.storage.stratis2.pool.r1"
    _FS_IFACE = "org.storage.stratis2.filesystem"
    _BLKDEV_IFACE = "org.storage.stratis2.blockdev"

    _DBUS_TIMEOUT_SECONDS = 120
    _TIMEOUT = _get_timeout(
        os.environ.get("STRATIS_DBUS_TIMEOUT", _DBUS_TIMEOUT_SECONDS * 1000)
    )

    @staticmethod
    def get_managed_objects():
        """
        Get managed objects for stratis
        :return: A dict,  Keys are object paths with dicts containing interface
                          names mapped to property dicts.
                          Property dicts map names to values.
        """
        object_manager = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, StratisDbus._TOP_OBJECT),
            StratisDbus._OBJECT_MANAGER,
        )
        return object_manager.GetManagedObjects(timeout=StratisDbus._TIMEOUT)

    @staticmethod
    def stratisd_version():
        """
        Get stratisd version
        :return: The current stratisd version
        :rtype: str
        """
        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, StratisDbus._TOP_OBJECT),
            dbus.PROPERTIES_IFACE,
        )
        return iface.Get(
            StratisDbus._MNGR_IFACE, "Version", timeout=StratisDbus._TIMEOUT
        )

    @staticmethod
    def pool_list():
        """
        Query the pools
        :return: A list of pool names
        :rtype: List of str
        """
        pool_objects = [
            obj_data[StratisDbus._POOL_IFACE]
            for _, obj_data in StratisDbus.get_managed_objects().items()
            if StratisDbus._POOL_IFACE in obj_data
            and obj_data[StratisDbus._POOL_IFACE]["Name"].startswith(TEST_PREF)
        ]

        return [pool_obj["Name"] for pool_obj in pool_objects]

    @staticmethod
    def blockdev_list():
        """
        Query the blockdevs
        :return: A list of blockdev names
        :rtype: List of str
        """
        blockdev_objects = [
            obj_data[StratisDbus._BLKDEV_IFACE]
            for _, obj_data in StratisDbus.get_managed_objects().items()
            if StratisDbus._BLKDEV_IFACE in obj_data
            and obj_data[StratisDbus._BLKDEV_IFACE]["Name"].startswith(TEST_PREF)
        ]

        return [blockdev_obj["Name"] for blockdev_obj in blockdev_objects]

    @staticmethod
    def set_key(key_desc, temp_file):
        """
        Set a key
        :param str key_desc: The key description
        :param temp_file:
        """
        manager_iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, StratisDbus._TOP_OBJECT),
            StratisDbus._MNGR_IFACE,
        )

        with open(temp_file.name, "r") as fd_for_dbus:
            return manager_iface.SetKey(key_desc, fd_for_dbus.fileno(), False)

    @staticmethod
    def unset_key(key_desc):
        """
        Unset a key
        """
        manager_iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, StratisDbus._TOP_OBJECT),
            StratisDbus._MNGR_IFACE,
        )

        return manager_iface.UnsetKey(key_desc)

    @staticmethod
    def pool_create(pool_name, devices, key_desc):
        """
        Create a pool
        :param str pool_name: The name of the pool to create
        :param str devices: A list of devices that can be used to create the pool
        :param key_desc: Key description
        :type key_desc: str or NoneType
        :return: The return values of the CreatePool call
        :rtype: The D-Bus types (b(oao)), q, and s
        """
        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, StratisDbus._TOP_OBJECT),
            StratisDbus._MNGR_IFACE,
        )
        return iface.CreatePool(
            pool_name,
            (dbus.Boolean(False), dbus.UInt16(0)),
            devices,
            (True, key_desc) if key_desc is not None else (False, ""),
            timeout=StratisDbus._TIMEOUT,
        )

    @staticmethod
    def pool_destroy(pool_name):
        """
        Destroy a pool
        :param str pool_name: The name of the pool to destroy
        :return: The object path of the DestroyPool call, or None
        :rtype: The D-Bus types (bs), q, and s, or None
        """
        pool_objects = {
            path: obj_data[StratisDbus._POOL_IFACE]
            for path, obj_data in StratisDbus.get_managed_objects().items()
            if StratisDbus._POOL_IFACE in obj_data
            and obj_data[StratisDbus._POOL_IFACE]["Name"].startswith(TEST_PREF)
        }

        pool_paths = [
            path
            for path, pool_obj in pool_objects.items()
            if pool_obj["Name"] == pool_name
        ]
        if pool_paths == []:
            return None

        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, StratisDbus._TOP_OBJECT),
            StratisDbus._MNGR_IFACE,
        )
        return iface.DestroyPool(pool_paths[0], timeout=StratisDbus._TIMEOUT)

    @staticmethod
    def fs_list():
        """
        Query the file systems
        :return: A dict,  Key being the fs name, the value being the pool name
        :rtype: dict mapping str to str
        """
        objects = StratisDbus.get_managed_objects().items()

        fs_objects = [
            obj_data[StratisDbus._FS_IFACE]
            for _, obj_data in objects
            if StratisDbus._FS_IFACE in obj_data
            and obj_data[StratisDbus._FS_IFACE]["Name"].startswith(TEST_PREF)
        ]

        pool_path_to_name = {
            obj: obj_data[StratisDbus._POOL_IFACE]["Name"]
            for obj, obj_data in objects
            if StratisDbus._POOL_IFACE in obj_data
            and obj_data[StratisDbus._POOL_IFACE]["Name"].startswith(TEST_PREF)
        }

        return {
            fs_object["Name"]: pool_path_to_name[fs_object["Pool"]]
            for fs_object in fs_objects
        }

    @staticmethod
    def pool_init_cache(pool_path, devices):
        """
        Initialize the cache for a pool with a list of devices.
        :param str pool_path: The object path of the pool to which the cache device will be added
        :param str devices: A list of devices that can be initialized as a cache device
        :return: The return values of the InitCache call
        :rtype: The D-Bus types (bao), q, and s
        """
        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, pool_path),
            StratisDbus._POOL_IFACE,
        )
        return iface.InitCache(devices, timeout=StratisDbus._TIMEOUT)

    @staticmethod
    def pool_add_cache(pool_path, devices):
        """
        Add a block device as a cache device
        :param str pool_path: The object path of the pool to which the cache device will be added
        :param str devices: A list of devices that can be added as a cache device
        :return: The return values of the AddCacheDevs call
        :rtype: The D-Bus types (bao), q, and s
        """
        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, pool_path),
            StratisDbus._POOL_IFACE,
        )
        return iface.AddCacheDevs(devices, timeout=StratisDbus._TIMEOUT)

    @staticmethod
    def pool_add_data(pool_path, devices):
        """
        Add a disk to an existing pool
        :param str pool_path: The object path of the pool to which the data device will be added
        :param str devices: A list of devices that can be added as a data device
        :return: The return values of the AddCacheDevs call
        :rtype: The D-Bus types (bao), q, and s
        """
        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, pool_path),
            StratisDbus._POOL_IFACE,
        )
        return iface.AddDataDevs(devices, timeout=StratisDbus._TIMEOUT)

    @staticmethod
    def fs_create(pool_path, fs_name):
        """
        Create a filesystem
        :param str pool_path: The object path of the pool in which the filesystem will be created
        :param str fs_name: The name of the filesystem to create
        :return: The return values of the CreateFilesystems call
        :rtype: The D-Bus types (ba(os)), q, and s
        """
        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, pool_path),
            StratisDbus._POOL_IFACE,
        )

        return iface.CreateFilesystems([fs_name], timeout=StratisDbus._TIMEOUT)

    @staticmethod
    def fs_destroy(pool_name, fs_name):
        """
        Destroy a filesystem
        :param str pool_name: The name of the pool which contains the filesystem
        :param str fs_name: The name of the filesystem to destroy
        :return: The return values of the DestroyFilesystems call, or None
        :rtype: The D-Bus types (bas), q, and s, or None
        """
        objects = StratisDbus.get_managed_objects().items()

        pool_objects = {
            path: obj_data[StratisDbus._POOL_IFACE]
            for path, obj_data in objects
            if StratisDbus._POOL_IFACE in obj_data
            and obj_data[StratisDbus._POOL_IFACE]["Name"].startswith(TEST_PREF)
        }
        fs_objects = {
            path: obj_data[StratisDbus._FS_IFACE]
            for path, obj_data in objects
            if StratisDbus._FS_IFACE in obj_data
            and obj_data[StratisDbus._FS_IFACE]["Name"].startswith(TEST_PREF)
        }

        pool_paths = [
            path
            for path, pool_obj in pool_objects.items()
            if pool_obj["Name"] == pool_name
        ]
        if pool_paths == []:
            return None

        fs_paths = [
            path for path, fs_obj in fs_objects.items() if fs_obj["Name"] == fs_name
        ]
        if fs_paths == []:
            return None

        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, pool_paths[0]),
            StratisDbus._POOL_IFACE,
        )
        return iface.DestroyFilesystems(fs_paths, timeout=StratisDbus._TIMEOUT)

    @staticmethod
    def fs_rename(fs_name, fs_name_rename):
        """
        Rename a filesystem
        :param str fs_name: The name of the filesystem to be renamed
        :param str fs_name_rename: The new name that the snapshot will have
        :return: The return values of the SetName call, or None
        :rtype: The D-Bus types (bs), q, and s, or None
        """
        objects = StratisDbus.get_managed_objects().items()

        fs_objects = {
            path: obj_data[StratisDbus._FS_IFACE]
            for path, obj_data in objects
            if StratisDbus._FS_IFACE in obj_data
            and obj_data[StratisDbus._FS_IFACE]["Name"].startswith(TEST_PREF)
        }

        fs_paths = [
            path for path, fs_obj in fs_objects.items() if fs_obj["Name"] == fs_name
        ]
        if fs_paths == []:
            return None

        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, fs_paths[0]),
            StratisDbus._FS_IFACE,
        )
        return iface.SetName(fs_name_rename, timeout=StratisDbus._TIMEOUT)

    @staticmethod
    def fs_snapshot(pool_path, fs_path, snapshot_name):
        """
        Snapshot a filesystem
        :param str pool_path: The object path of the pool containing the fs
        :param str fs_name: The object path of the filesystem to snapshot
        :param str snapshot_name: The name of the snapshot to be made
        :return: The return values of the SnapshotFilesystem call
        :rtype: The D-Bus types (bo), q, and s
        """
        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, pool_path),
            StratisDbus._POOL_IFACE,
        )
        return iface.SnapshotFilesystem(
            fs_path, snapshot_name, timeout=StratisDbus._TIMEOUT
        )

    @staticmethod
    def destroy_all():
        """
        Destroys all Stratis FS and pools!
        :return: None
        """
        umount_mdv()

        # Remove FS
        for name, pool_name in StratisDbus.fs_list().items():
            StratisDbus.fs_destroy(pool_name, name)

        # Remove Pools
        for name in StratisDbus.pool_list():
            StratisDbus.pool_destroy(name)

    @staticmethod
    def get_report(report_name):
        """
        Get the report with the given name.
        :param str report_name: The name of the report
        :return: The JSON report as a string with a status code and string
        :rtype: The D-Bus types s, q, and s
        """
        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, StratisDbus._TOP_OBJECT),
            StratisDbus._REPORT_IFACE,
        )
        return iface.GetReport(report_name, timeout=StratisDbus._TIMEOUT)


def clean_up():
    """
    Try to clean up after a test failure.

    :return: None
    """
    StratisDbus.destroy_all()
    remnant_pools = StratisDbus.pool_list()
    if remnant_pools != []:
        raise RuntimeError(
            "testlib dbus: clean_up failed; remnant pools: %s"
            % ", ".join(remnant_pools)
        )
