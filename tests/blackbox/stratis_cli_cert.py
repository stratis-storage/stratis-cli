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
Tests of the stratis CLI.
"""

import argparse
import sys
import time
import unittest

from testlib.utils import exec_command, exec_test_command, process_exists, p_n, fs_n
from testlib.stratis import STRATIS_CLI, StratisCli, clean_up

DISKS = []


def make_test_pool():
    """
    Create a test pool that will later get destroyed
    :return: Name of the created pool
    """
    pool_name = p_n()
    exec_test_command([STRATIS_CLI, "pool", "create", pool_name, DISKS[0]])
    return pool_name


def make_test_filesystem(pool_name):
    """
    Create a test filesystem that will later get destroyed
    :param name: Name of a test pool
    :return: Name of the created filesystem
    """
    filesystem_name = fs_n()
    assert (
        exec_test_command(
            [STRATIS_CLI, "filesystem", "create", pool_name, filesystem_name]
        )[0]
        == 0
    )
    return filesystem_name


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

        StratisCli.destroy_all()
        assert StratisCli.pool_list() == []

    def test_stratisd_version(self):
        """
        Test getting the daemon version.
        """
        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "daemon", "version"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertNotEqual(stdout, "")

    def test_stratisd_redundancy(self):
        """
        Test listing the redundancy levels that the Stratis service supports.
        """
        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "daemon", "redundancy"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertNotEqual(stdout, "")

    def test_pool_list_empty(self):
        """
        Test listing a non-existent pool.
        """
        exit_code, stdout, stderr = exec_test_command([STRATIS_CLI, "pool", "list"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertNotEqual(stdout, "")

    def test_filesystem_list_empty(self):
        """
        Test listing an non-existent filesystem.
        """
        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "filesystem", "list"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertNotEqual(stdout, "")

    def test_pool_create(self):
        """
        Test creating a pool.
        """
        pool_name = p_n()
        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "pool", "create", pool_name, DISKS[0]]
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")

    def test_pool_list_not_empty(self):
        """
        Test listing an existent pool.
        """
        make_test_pool()

        exit_code, stdout, stderr = exec_test_command([STRATIS_CLI, "pool", "list"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertNotEqual(stdout, "")

    def test_blockdev_list(self):
        """
        Test listing a blockdev.
        """
        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "blockdev", "list", make_test_pool()]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertNotEqual(stdout, "")

    def test_pool_create_same_name(self):
        """
        Test creating a pool that already exists.
        """
        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "pool", "create", make_test_pool(), DISKS[0]]
        )
        self.assertEqual(exit_code, 1)
        self.assertNotEqual(stderr, "")
        self.assertEqual(stdout, "")

    def test_pool_add_cache(self):
        """
        Test adding cache to a pool.
        """
        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "pool", "add-cache", make_test_pool(), DISKS[1]]
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")

    def test_pool_destroy(self):
        """
        Test destroying a pool.
        """
        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "pool", "destroy", make_test_pool()]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")

    def test_filesystem_create(self):
        """
        Test creating a filesystem.
        """
        filesystem_name = fs_n()
        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "filesystem", "create", make_test_pool(), filesystem_name]
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")

    def test_pool_add_data(self):
        """
        Test adding data to a pool.
        """
        pool_name = make_test_pool()
        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "pool", "add-data", pool_name, DISKS[1]]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")

    def test_filesystem_list_not_empty(self):
        """
        Test listing an existent filesystem.
        """
        pool_name = make_test_pool()
        make_test_filesystem(pool_name)

        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "filesystem", "list"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertNotEqual(stdout, "")

    def test_filesystem_create_same_name(self):
        """
        Test creating a filesystem that already exists.
        """
        pool_name = make_test_pool()
        filesystem_name = make_test_filesystem(pool_name)

        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "filesystem", "create", pool_name, filesystem_name]
        )

        self.assertEqual(exit_code, 1)
        self.assertNotEqual(stderr, "")
        self.assertEqual(stdout, "")

    def test_filesystem_rename(self):
        """
        Test renaming a filesystem to a new name.
        """
        pool_name = make_test_pool()
        filesystem_name = make_test_filesystem(pool_name)
        fs_name_rename = fs_n()

        exit_code, stdout, stderr = exec_test_command(
            [
                STRATIS_CLI,
                "filesystem",
                "rename",
                pool_name,
                filesystem_name,
                fs_name_rename,
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")

    def test_filesystem_rename_same_name(self):
        """
        Test renaming a filesystem to the same name.
        """
        pool_name = make_test_pool()
        filesystem_name = make_test_filesystem(pool_name)

        exit_code, stdout, stderr = exec_test_command(
            [
                STRATIS_CLI,
                "filesystem",
                "rename",
                pool_name,
                filesystem_name,
                filesystem_name,
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")

    def test_filesystem_snapshot(self):
        """
        Test renaming a filesystem to the same name.
        """
        pool_name = make_test_pool()
        filesystem_name = make_test_filesystem(pool_name)

        snapshot_name = fs_n()

        exit_code, stdout, stderr = exec_test_command(
            [
                STRATIS_CLI,
                "filesystem",
                "snapshot",
                pool_name,
                filesystem_name,
                snapshot_name,
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")

    def test_filesystem_destroy(self):
        """
        Test destroying a filesystem.
        """
        pool_name = make_test_pool()
        filesystem_name = make_test_filesystem(pool_name)

        exit_code, stdout, stderr = exec_test_command(
            [STRATIS_CLI, "filesystem", "destroy", pool_name, filesystem_name]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")


if __name__ == "__main__":
    ARGUMENT_PARSER = argparse.ArgumentParser()
    ARGUMENT_PARSER.add_argument(
        "--disk", action="append", dest="DISKS", help="disks to use", required=True
    )
    PARSED_ARGS, OTHER_ARGS = ARGUMENT_PARSER.parse_known_args()
    DISKS = PARSED_ARGS.DISKS
    print("Using block device(s) for tests: %s" % DISKS)
    unittest.main(argv=sys.argv[:1] + OTHER_ARGS)
