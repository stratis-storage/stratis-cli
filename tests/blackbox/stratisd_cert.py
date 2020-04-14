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
Tests of stratisd.
"""

# isort: STDLIB
import argparse
import sys
import time
import unittest

# isort: THIRDPARTY
import dbus
from testlib.dbus import StratisDbus, clean_up
from testlib.utils import exec_command, fs_n, p_n, process_exists


def make_test_pool(pool_name, pool_disks):
    """
    Create a test pool that will later get destroyed
    :param str pool_name: Name of the pool to be created
    :param list pool_disks: List of disks with which the pool will be created
    :return: Object path of the created pool
    """
    (obj_path_exists, (obj_path, _)), return_code, msg = StratisDbus.pool_create(
        pool_name, pool_disks, None
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
        * Call "udevadm settle" so udev database can be updated with changes
        to Stratis devices.
        :return: None
        """
        self.addCleanup(clean_up)

        if process_exists("stratisd") is None:
            exec_command(["systemctl", "start", "stratisd"])
            time.sleep(20)

        clean_up()

        time.sleep(1)
        exec_command(["udevadm", "settle"])

    def test_get_managed_objects(self):
        """
        Test that GetManagedObjects returns a dict w/out failure.
        """
        result = StratisDbus.get_managed_objects()
        self.assertIsInstance(result, dict)

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
        (_, return_code, _) = StratisDbus.pool_create(
            pool_name, StratisCertify.DISKS, None
        )
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_pool_add_cache(self):
        """
        Test adding cache to a pool.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        (_, return_code, _) = StratisDbus.pool_init_cache(
            pool_path, StratisCertify.DISKS[1:2]
        )
        self.assertEqual(return_code, dbus.UInt16(0))
        (_, return_code, _) = StratisDbus.pool_add_cache(
            pool_path, StratisCertify.DISKS[2:3]
        )
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_pool_add_data(self):
        """
        Test adding data to a pool.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:2])

        (_, return_code, _) = StratisDbus.pool_add_data(
            pool_path, StratisCertify.DISKS[2:3]
        )
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_pool_list_not_empty(self):
        """
        Test listing an non-existent pool.
        """
        pool_name = p_n()
        make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        result = StratisDbus.pool_list()
        self.assertIsInstance(result, list)
        self.assertNotEqual(result, [])

    def test_pool_create_same_name_and_devices(self):
        """
        Test creating a pool that already exists with the same devices.
        """
        pool_name = p_n()
        make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        (_, return_code, _) = StratisDbus.pool_create(
            pool_name, StratisCertify.DISKS[0:1], None
        )
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_pool_create_same_name_different_devices(self):
        """
        Test creating a pool that already exists with different devices.
        """
        pool_name = p_n()
        make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        (_, return_code, _) = StratisDbus.pool_create(
            pool_name, StratisCertify.DISKS[1:3], None
        )
        self.assertEqual(return_code, dbus.UInt16(1))

    def test_pool_destroy(self):
        """
        Test destroying a pool.
        """
        pool_name = p_n()
        make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        (_, return_code, _) = StratisDbus.pool_destroy(pool_name)
        self.assertEqual(return_code, dbus.UInt16(0))

        self.assertEqual(StratisDbus.fs_list(), {})

    def test_filesystem_create(self):
        """
        Test creating a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()

        (_, return_code, _) = StratisDbus.fs_create(pool_path, fs_name)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_filesystem_rename(self):
        """
        Test renaming a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

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
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        (_, return_code, _) = StratisDbus.fs_rename(fs_name, fs_name)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_filesystem_snapshot(self):
        """
        Test snapshotting a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

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
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

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
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        (_, return_code, _) = StratisDbus.fs_create(pool_path, fs_name)
        self.assertEqual(return_code, dbus.UInt16(0))

    def test_filesystem_destroy(self):
        """
        Test destroying a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        (_, return_code, _) = StratisDbus.fs_destroy(pool_name, fs_name)
        self.assertEqual(return_code, dbus.UInt16(0))

        self.assertEqual(StratisDbus.fs_list(), {})


def main():
    """
    The main method.
    """
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "--disk",
        action="append",
        dest="DISKS",
        default=[],
        help="disks to use, a minimum of 3 in order to run every test",
    )
    parsed_args, unittest_args = argument_parser.parse_known_args()
    StratisCertify.DISKS = parsed_args.DISKS
    print("Using block device(s) for tests: %s" % StratisCertify.DISKS)
    unittest.main(argv=sys.argv[:1] + unittest_args)


if __name__ == "__main__":
    main()
