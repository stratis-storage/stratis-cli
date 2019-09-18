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
import dbus

from .utils import umount_mdv


class StratisDbus:
    "Wrappers around stratisd DBus calls"

    _OBJECT_MANAGER = "org.freedesktop.DBus.ObjectManager"
    _BUS = dbus.SystemBus()
    _BUS_NAME = "org.storage.stratis1"
    _TOP_OBJECT = "/org/storage/stratis1"

    _MNGR_IFACE = "org.storage.stratis1.Manager"
    _POOL_IFACE = "org.storage.stratis1.pool"
    _FS_IFACE = "org.storage.stratis1.filesystem"

    @staticmethod
    def _get_managed_objects():
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
        return object_manager.GetManagedObjects()

    @staticmethod
    def pool_list():
        """
        Query the pools
        :return: A list of pool names.
        """
        pool_objects = [
            obj_data[StratisDbus._POOL_IFACE]
            for _, obj_data in StratisDbus._get_managed_objects().items()
            if StratisDbus._POOL_IFACE in obj_data
        ]

        return [pool_obj["Name"] for pool_obj in pool_objects]

    @staticmethod
    def pool_destroy(pool_name):
        """
        Destroy a pool
        :param name: Name of pool to destroy
        :return: None
        """
        pool_objects = {
            path: obj_data[StratisDbus._POOL_IFACE]
            for path, obj_data in StratisDbus._get_managed_objects().items()
            if StratisDbus._POOL_IFACE in obj_data
        }

        pool_object_paths = [
            path
            for path, pool_obj in pool_objects.items()
            if pool_obj["Name"] == pool_name
        ]
        if pool_object_paths == []:
            return None

        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, StratisDbus._TOP_OBJECT),
            StratisDbus._MNGR_IFACE,
        )
        iface.DestroyPool(pool_object_paths[0])

        return None

    @staticmethod
    def fs_list():
        """
        Query the file systems
        :return: A dict,  Key being the fs name, the value being a dict with
                          keys [POOL_NAME, USED_SIZE, UUID, SYM_LINK, CREATED,
                                CREATED_TS]
        """
        objects = StratisDbus._get_managed_objects().items()

        fs_objects = [
            obj_data[StratisDbus._FS_IFACE]
            for _, obj_data in objects
            if StratisDbus._FS_IFACE in obj_data
        ]

        pool_path_to_name = {
            obj: obj_data[StratisDbus._POOL_IFACE]["Name"]
            for obj, obj_data in objects
            if StratisDbus._POOL_IFACE in obj_data
        }

        result = {
            fs_object["Name"]: pool_path_to_name[fs_object["Pool"]]
            for fs_object in fs_objects
        }

        return result

    @staticmethod
    def fs_destroy(pool_name, fs_name):
        """
        Destroy a FS
        :param pool_name:  Pool which contains the FS
        :param fs_name: Name of FS to destroy
        :return: None
        """
        objects = StratisDbus._get_managed_objects().items()

        pool_objects = {
            path: obj_data[StratisDbus._POOL_IFACE]
            for path, obj_data in objects
            if StratisDbus._POOL_IFACE in obj_data
        }
        fs_objects = {
            path: obj_data[StratisDbus._FS_IFACE]
            for path, obj_data in objects
            if StratisDbus._FS_IFACE in obj_data
        }

        pool_object_paths = [
            path
            for path, pool_obj in pool_objects.items()
            if pool_obj["Name"] == pool_name
        ]
        if pool_object_paths == []:
            return None

        fs_object_paths = [
            path for path, fs_obj in fs_objects.items() if fs_obj["Name"] == fs_name
        ]
        if fs_object_paths == []:
            return None

        iface = dbus.Interface(
            StratisDbus._BUS.get_object(StratisDbus._BUS_NAME, pool_object_paths[0]),
            StratisDbus._POOL_IFACE,
        )
        iface.DestroyFilesystems(fs_object_paths)

        return None

    @staticmethod
    def destroy_all():
        """
        Destroys all Stratis FS and pools!
        :return: None
        """
        umount_mdv()

        # Remove FS
        for name, filesystem in StratisDbus.fs_list().items():
            StratisDbus.fs_destroy(filesystem["POOL_NAME"], name)

        # Remove Pools
        for name in StratisDbus.pool_list():
            StratisDbus.pool_destroy(name)


def clean_up():
    """
    Try to clean up after a test failure.

    :return: None
    """
    StratisDbus.destroy_all()
    assert StratisDbus.pool_list() == []
