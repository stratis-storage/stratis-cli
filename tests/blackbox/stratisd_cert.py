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
Tests of stratisd via the Stratis CLI.
"""

import argparse
import sys
import time
import unittest

import dbus

from testlib.dbus import StratisDbus, clean_up
from testlib.utils import exec_command, exec_test_command, process_exists, p_n, fs_n

DISKS = []


def make_test_pool(pool_name):
    """
    Create a test pool that will later get destroyed
    :return: Object path of the created pool
    """
    (obj_path_exists, (obj_path, _)), return_code, _ = StratisDbus.pool_create(pool_name, DISKS)
    if obj_path_exists == dbus.Boolean(False) or return_code == dbus.UInt16(1):
        print("Failed to create pool.")
    else:
        print("The path is: ")
        print(obj_path)
        return obj_path

def make_test_filesystem(pool_object_path):
    """
    Create a test filesystem that will later get destroyed
    :param pool_name: Object path of a test pool
    :return: Object path of the created pool
    """
    filesystem_name = fs_n()
    (obj_path_exists, (obj_path, _)), return_code, _ = StratisDbus.filesystem_create(pool_object_path, filesystem_name)
    if obj_path_exists == dbus.Boolean(False) or return_code == dbus.UInt16(1):
        print("Failed to create filesystem.")
    else:
        return obj_path

class StratisCertify(unittest.TestCase):
    """
    Unit tests for Stratis
    """

    def setUp(self):
        """
        Setup for an individual test.
        * Register a cleanup action, to be run if the test fails.
        * Ensure that stratisd is running via systemd.
        * Use the running stratisd instance to destroy any existing
        Stratis filesystems, pools, etc.
        :return: None
        """
        self.addCleanup(clean_up)

        if process_exists("stratisd") is None:
            exec_command(["systemctl", "start", "stratisd"])
            time.sleep(20)

        StratisDbus.destroy_all()
        assert StratisDbus.pool_list() == []

    def test_get_managed_objects(self):
        """
        Test that GetManagedObjects returns a string w/out failure.
        """
        exit_code, stdout, stderr = exec_test_command(
            [
                "busctl",
                "call",
                "org.storage.stratis1",
                "/org/storage/stratis1",
                "org.freedesktop.DBus.ObjectManager",
                "GetManagedObjects",
                "--verbose",
                "--no-pager",
                "--timeout=1200",
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertNotEqual(stdout, "")

    def test_stratisd_version(self):
        """
        Test getting the daemon version.
        """
        self.assertNotEqual(StratisDbus.stratisd_version(), [])

    def test_stratisd_redundancy(self):
        """
        Test listing the redundancy levels that the Stratis service supports.
        """
        self.assertNotEqual(StratisDbus.stratisd_redundancy(), [])

    def test_pool_list_empty(self):
        """
        Test listing an non-existent pool.
        """
        self.assertEqual(StratisDbus.pool_list(), [])

    def test_blockdev_list(self):
        """
        Test listing a blockdev.
        """
        self.assertEqual(StratisDbus.blockdev_list(), [])

    def test_filesystem_list_empty(self):
        """
        Test listing an non-existent filesystem.
        """
        self.assertEqual(StratisDbus.fs_list(), {})

    def test_pool_create(self):
        """
        Test creating a pool.
        """
        pool_name = p_n()
        self.assertEqual(StratisDbus.pool_create(pool_name, DISKS)[1], dbus.UInt16(0))

    # def test_pool_add_cache(self):
    #     """
    #     Test adding cache to a pool.
    #     """
    #     pool_name = p_n()
    #     make_test_pool(pool_name)
    #     self.assertEqual(
    #         StratisDbus.pool_add_cache(pool_name, DISKS)[1], dbus.UInt16(0)
    #     )

    def test_pool_add_data(self):
        """
        Test adding data to a pool.
        """
        pool_name = p_n()
        make_test_pool(pool_name)
        self.assertEqual(StratisDbus.pool_add_data(pool_name, DISKS)[1], dbus.UInt16(0))

    def test_pool_list_not_empty(self):
        """
        Test listing an non-existent pool.
        """
        pool_name = p_n()
        make_test_pool(pool_name)
        self.assertNotEqual(StratisDbus.pool_list(), [])

    def test_pool_create_same_name(self):
        """
        Test creating a pool that already exists.
        """
        pool_name = p_n()
        self.assertEqual(StratisDbus.pool_create(pool_name, DISKS)[1], dbus.UInt16(0))

    def test_pool_destroy(self):
        """
        Test destroying a pool.
        """
        pool_name = p_n()
        make_test_pool(pool_name)
        self.assertEqual(StratisDbus.pool_destroy(pool_name)[1], dbus.UInt16(0))
        self.assertEqual(StratisDbus.fs_list(), {})

    def test_filesystem_create(self):
        """
        Test creating a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name)
        filesystem_name = fs_n()
        self.assertEqual(
            StratisDbus.filesystem_create(pool_path, filesystem_name)[1], dbus.UInt16(0)
        )

    # def test_filesystem_rename(self):
    #     """
    #     Test renaming a filesystem.
    #     """
    #     pool_name = p_n()
    #     pool_path = make_test_pool(pool_name)
    #     filesystem_name = fs_n()
    #     filesystem_name_rename = fs_n()
    #     assert StratisDbus.filesystem_create(pool_path, filesystem_name)
    #     self.assertEqual(
    #         StratisDbus.filesystem_rename(
    #             pool_name, filesystem_name, filesystem_name_rename
    #         )[1],
    #         dbus.UInt16(0),
    #     )

    # def test_filesystem_rename_same_name(self):
    #     """
    #     Test renaming a filesystem.
    #     """
    #     pool_name = make_test_pool()
    #     filesystem_name = fs_n()
    #     assert StratisDbus.filesystem_create(pool_name, filesystem_name)
    #     self.assertEqual(
    #         StratisDbus.filesystem_rename(pool_name, filesystem_name, filesystem_name)[
    #             1
    #         ],
    #         dbus.UInt16(0),
    #     )

    # def test_filesystem_snapshot(self):
    #     """
    #     Test snapshotting a filesystem.
    #     """
    #     pool_name = p_n()
    #     pool_path = make_test_pool(pool_name)
    #     filesystem_name = fs_n()
    #     snapshot_name = fs_n()
    #     assert StratisDbus.filesystem_create(pool_path, filesystem_name)
    #     self.assertEqual(
    #         StratisDbus.filesystem_snapshot(pool_name, filesystem_name, snapshot_name)[
    #             1
    #         ],
    #         dbus.UInt16(0),
    #     )

    # def test_filesystem_list_not_empty(self):
    #     """
    #     Test listing an existent filesystem.
    #     """
    #     pool_name = p_n()
    #     pool_path = make_test_pool(pool_name)
    #     make_test_filesystem(pool_name)
    #     self.assertNotEqual(StratisDbus.fs_list(), [])

    # def test_filesystem_create_same_name(self):
    #     """
    #     Test creating a filesystem that already exists.
    #     """
    #     pool_name = p_n()
    #     pool_path = make_test_pool(pool_name)
    #     filesystem_name = make_test_filesystem(pool_name)
    #     self.assertNotEqual(
    #         StratisDbus.filesystem_create(pool_name, filesystem_name), []
    #     )

    # def test_filesystem_destroy(self):
    #     """
    #     Test destroying a filesystem.
    #     """
    #     pool_name = p_n()
    #     pool_path = make_test_pool(pool_name)
    #     filesystem_name = make_test_filesystem(pool_name)
    #     self.assertEqual(
    #         StratisDbus.fs_destroy(pool_name, filesystem_name)[1], dbus.UInt16(0)
    #     )
    #     self.assertEqual(StratisDbus.fs_list(), {})


if __name__ == "__main__":
    ARGUMENT_PARSER = argparse.ArgumentParser()
    ARGUMENT_PARSER.add_argument(
        "--disk", action="append", dest="DISKS", help="disks to use", required=True
    )
    PARSED_ARGS, OTHER_ARGS = ARGUMENT_PARSER.parse_known_args()
    DISKS = PARSED_ARGS.DISKS
    print("Using block device(s) for tests: %s" % DISKS)
    unittest.main(argv=sys.argv[:1] + OTHER_ARGS)
