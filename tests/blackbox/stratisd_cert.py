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
    :param str pool_name: Name of the pool to be created
    :return: Object path of the created pool
    """
    pool_disk = DISKS[0:1]
    (obj_path_exists, (obj_path, _)), return_code, msg = StratisDbus.pool_create(
        pool_name, pool_disk
    )
    assert return_code == 0, "return_code: %s, error_msg: %s" % (return_code, msg)
    assert obj_path_exists, "obj_path_exists: %s" % obj_path_exists
    return obj_path


def make_test_filesystem(pool_path, fs_name):
    """
    Create a test filesystem that will later get destroyed
    :param str pool_path: Object path of a test pool
    :param str fs_name: Name of the filesystem to be created
    :return: Object path of the created filesystem
    """
    (
        filesystems_created,
        (array_of_tuples_with_obj_paths_and_names),
    ), return_code, msg = StratisDbus.fs_create(pool_path, fs_name)
    assert return_code == 0, "return_code: %s, error_msg: %s" % (return_code, msg)
    assert filesystems_created, "filesystems_created: %s" % filesystems_created
    return array_of_tuples_with_obj_paths_and_names[0][0]


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
        result = StratisDbus.stratisd_version()
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "")

    def test_pool_list_empty(self):
        """
        Test listing an non-existent pool.
        """
        result = StratisDbus.pool_list()
        self.assertIsInstance(result, list)
        self.assertEqual(result, [])

    def test_blockdev_list(self):
        """
        Test listing a blockdev.
        """
        result = StratisDbus.blockdev_list()
        self.assertIsInstance(result, list)
        self.assertEqual(result, [])

    def test_filesystem_list_empty(self):
        """
        Test listing an non-existent filesystem.
        """
        result = StratisDbus.fs_list()
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_pool_create(self):
        """
        Test creating a pool.
        """
        pool_name = p_n()
        (_, return_code, _) = StratisDbus.pool_create(pool_name, DISKS)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_pool_add_cache(self):
        """
        Test adding cache to a pool.
        """
        cache_disks = DISKS[1:2]

        pool_name = p_n()
        pool_path = make_test_pool(pool_name)

        (_, return_code, _) = StratisDbus.pool_add_cache(pool_path, cache_disks)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_pool_add_data(self):
        """
        Test adding data to a pool.
        """
        data_disks = DISKS[2:3]

        pool_name = p_n()
        pool_path = make_test_pool(pool_name)

        (_, return_code, _) = StratisDbus.pool_add_data(pool_path, data_disks)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_pool_list_not_empty(self):
        """
        Test listing an non-existent pool.
        """
        pool_name = p_n()
        make_test_pool(pool_name)

        result = StratisDbus.pool_list()
        self.assertIsInstance(result, list)
        self.assertNotEqual(result, [])

    def test_pool_create_same_name(self):
        """
        Test creating a pool that already exists.
        """
        pool_disks = DISKS[1:3]

        pool_name = p_n()
        make_test_pool(pool_name)

        (_, return_code, _) = StratisDbus.pool_create(pool_name, pool_disks)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_pool_destroy(self):
        """
        Test destroying a pool.
        """
        pool_name = p_n()
        make_test_pool(pool_name)

        (_, return_code, _) = StratisDbus.pool_destroy(pool_name)
        self.assertEqual(return_code, dbus.UInt16(0))

        self.assertEqual(StratisDbus.fs_list(), {})

    def test_filesystem_create(self):
        """
        Test creating a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name)

        fs_name = fs_n()

        (_, return_code, _) = StratisDbus.fs_create(pool_path, fs_name)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_filesystem_rename(self):
        """
        Test renaming a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name)

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        fs_name_rename = fs_n()

        (_, return_code, _) = StratisDbus.fs_rename(fs_name, fs_name_rename)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_filesystem_rename_same_name(self):
        """
        Test renaming a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name)

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        (_, return_code, _) = StratisDbus.fs_rename(fs_name, fs_name)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_filesystem_snapshot(self):
        """
        Test snapshotting a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name)

        fs_name = fs_n()
        fs_path = make_test_filesystem(pool_path, fs_name)

        snapshot_name = fs_n()

        (_, return_code, _) = StratisDbus.fs_snapshot(pool_path, fs_path, snapshot_name)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_filesystem_list_not_empty(self):
        """
        Test listing an existent filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name)

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        result = StratisDbus.fs_list()
        self.assertIsInstance(result, dict)
        self.assertNotEqual(result, {})

    def test_filesystem_create_same_name(self):
        """
        Test creating a filesystem that already exists.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name)

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        (_, return_code, _) = StratisDbus.fs_create(pool_path, fs_name)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_filesystem_destroy(self):
        """
        Test destroying a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name)

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        (_, return_code, _) = StratisDbus.fs_destroy(pool_name, fs_name)
        self.assertEqual(return_code, dbus.UInt16(0))

        self.assertEqual(StratisDbus.fs_list(), {})


if __name__ == "__main__":
    ARGUMENT_PARSER = argparse.ArgumentParser()
    ARGUMENT_PARSER.add_argument(
        "--disk", action="append", dest="DISKS", help="disks to use", required=True
    )
    PARSED_ARGS, OTHER_ARGS = ARGUMENT_PARSER.parse_known_args()
    DISKS = PARSED_ARGS.DISKS
    print("Using block device(s) for tests: %s" % DISKS)
    unittest.main(argv=sys.argv[:1] + OTHER_ARGS)
