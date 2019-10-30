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
from testlib.stratis import STRATIS_CLI, clean_up

DISKS = []


def make_test_pool(pool_disks):
    """
    Create a test pool that will later get destroyed
    :param list pool_disks: List of disks with which the pool will be created
    :return: Name of the created pool
    """
    pool_name = p_n()
    (return_code, _, stderr) = exec_test_command(
        [STRATIS_CLI, "pool", "create", pool_name] + pool_disks
    )
    assert return_code == 0, "return_code: %s, stderr: %s" % (return_code, stderr)
    return pool_name


def make_test_filesystem(pool_name):
    """
    Create a test filesystem that will later get destroyed
    :param pool_name: Name of a test pool
    :return: Name of the created filesystem
    """
    filesystem_name = fs_n()
    (return_code, _, stderr) = exec_test_command(
        [STRATIS_CLI, "filesystem", "create", pool_name, filesystem_name]
    )
    assert return_code == 0, "return_code: %s, stderr: %s" % (return_code, stderr)
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
        * Call "udevadm settle" so udev database can be updated with changes
        to Stratis devices.
        :return: None
        """
        self.addCleanup(clean_up)

        if process_exists("stratisd") is None:
            exec_command(["systemctl", "start", "stratisd"])
            time.sleep(20)

        clean_up()

        exec_command(["udevadm", "settle"])

    def unittest_command(  # pylint: disable=bad-continuation
        self, args, exp_exit_code, exp_stderr_is_empty, exp_stdout_is_empty
    ):
        """
        Execute a test command and make assertions about the exit code, stderr, and stdout
        :param list args: The arguments needed to execute the Stratis command being tested
        :type args: List of str
        :param exp_exit_code: The expected exit code, 0, 1, or 2
        :param bool exp_stderr_is_empty: True if stderr is expected to be empty, otherwise False
        :param bool exp_stdout_is_empty: True if stdout is expected to be empty, otherwise False
        :return: None
        """
        exit_code, stdout, stderr = exec_test_command(args)

        self.assertEqual(exit_code, exp_exit_code)

        if exp_stderr_is_empty:
            self.assertEqual(stderr, "")
        else:
            self.assertNotEqual(stderr, "")

        if exp_stdout_is_empty:
            self.assertEqual(stdout, "")
        else:
            self.assertNotEqual(stdout, "")

    def test_stratisd_version(self):
        """
        Test getting the daemon version.
        """
        self.unittest_command([STRATIS_CLI, "daemon", "version"], 0, True, False)

    def test_stratisd_redundancy(self):
        """
        Test listing the redundancy levels that the Stratis service supports.
        """
        self.unittest_command([STRATIS_CLI, "daemon", "redundancy"], 0, True, False)

    def test_pool_list_empty(self):
        """
        Test listing a non-existent pool.
        """
        self.unittest_command([STRATIS_CLI, "pool", "list"], 0, True, False)

    def test_filesystem_list_empty(self):
        """
        Test listing an non-existent filesystem.
        """
        self.unittest_command([STRATIS_CLI, "filesystem", "list"], 0, True, False)

    def test_pool_create(self):
        """
        Test creating a pool.
        """
        pool_name = p_n()
        self.unittest_command(
            [STRATIS_CLI, "pool", "create", pool_name, DISKS[0]], 0, True, True
        )

    def test_pool_list_not_empty(self):
        """
        Test listing an existent pool.
        """
        make_test_pool(DISKS[0:1])
        self.unittest_command([STRATIS_CLI, "pool", "list"], 0, True, False)

    def test_blockdev_list(self):
        """
        Test listing a blockdev.
        """
        self.unittest_command([STRATIS_CLI, "blockdev", "list"], 0, True, False)

    def test_pool_create_same_name(self):
        """
        Test creating a pool that already exists.
        """
        self.unittest_command(
            [STRATIS_CLI, "pool", "create", make_test_pool(DISKS[0:1]), DISKS[1]],
            1,
            False,
            True,
        )

    def test_pool_add_cache(self):
        """
        Test adding cache to a pool.
        """
        self.unittest_command(
            [STRATIS_CLI, "pool", "add-cache", make_test_pool(DISKS[0:2]), DISKS[2]],
            0,
            1,
            True,
        )

    def test_pool_destroy(self):
        """
        Test destroying a pool.
        """
        self.unittest_command(
            [STRATIS_CLI, "pool", "destroy", make_test_pool(DISKS[0:1])], 0, True, True
        )

    def test_filesystem_create(self):
        """
        Test creating a filesystem.
        """
        filesystem_name = fs_n()
        self.unittest_command(
            [
                STRATIS_CLI,
                "filesystem",
                "create",
                make_test_pool(DISKS[0:1]),
                filesystem_name,
            ],
            0,
            True,
            True,
        )

    def test_pool_add_data(self):
        """
        Test adding data to a pool.
        """
        pool_name = make_test_pool(DISKS[0:1])
        self.unittest_command(
            [STRATIS_CLI, "pool", "add-data", pool_name, DISKS[1]], 0, True, True
        )

    def test_filesystem_list_not_empty(self):
        """
        Test listing an existent filesystem.
        """
        pool_name = make_test_pool(DISKS[0:1])
        make_test_filesystem(pool_name)
        self.unittest_command([STRATIS_CLI, "filesystem", "list"], 0, True, False)

    def test_filesystem_create_same_name(self):
        """
        Test creating a filesystem that already exists.
        """
        pool_name = make_test_pool(DISKS[0:1])
        filesystem_name = make_test_filesystem(pool_name)
        self.unittest_command(
            [STRATIS_CLI, "filesystem", "create", pool_name, filesystem_name],
            1,
            False,
            True,
        )

    def test_filesystem_rename(self):
        """
        Test renaming a filesystem to a new name.
        """
        pool_name = make_test_pool(DISKS[0:1])
        filesystem_name = make_test_filesystem(pool_name)
        fs_name_rename = fs_n()
        self.unittest_command(
            [
                STRATIS_CLI,
                "filesystem",
                "rename",
                pool_name,
                filesystem_name,
                fs_name_rename,
            ],
            0,
            True,
            True,
        )

    def test_filesystem_rename_same_name(self):
        """
        Test renaming a filesystem to the same name.
        """
        pool_name = make_test_pool(DISKS[0:1])
        filesystem_name = make_test_filesystem(pool_name)
        self.unittest_command(
            [
                STRATIS_CLI,
                "filesystem",
                "rename",
                pool_name,
                filesystem_name,
                filesystem_name,
            ],
            1,
            False,
            True,
        )

    def test_filesystem_snapshot(self):
        """
        Test snapshotting a filesystem.
        """
        pool_name = make_test_pool(DISKS[0:1])
        filesystem_name = make_test_filesystem(pool_name)
        snapshot_name = fs_n()
        self.unittest_command(
            [
                STRATIS_CLI,
                "filesystem",
                "snapshot",
                pool_name,
                filesystem_name,
                snapshot_name,
            ],
            0,
            True,
            True,
        )

    def test_filesystem_destroy(self):
        """
        Test destroying a filesystem.
        """
        pool_name = make_test_pool(DISKS[0:1])
        filesystem_name = make_test_filesystem(pool_name)
        self.unittest_command(
            [STRATIS_CLI, "filesystem", "destroy", pool_name, filesystem_name],
            0,
            True,
            True,
        )


if __name__ == "__main__":
    ARGUMENT_PARSER = argparse.ArgumentParser()
    ARGUMENT_PARSER.add_argument(
        "--disk", action="append", dest="DISKS", help="disks to use", required=True
    )
    PARSED_ARGS, OTHER_ARGS = ARGUMENT_PARSER.parse_known_args()
    DISKS = PARSED_ARGS.DISKS
    print("Using block device(s) for tests: %s" % DISKS)
    unittest.main(argv=sys.argv[:1] + OTHER_ARGS)
