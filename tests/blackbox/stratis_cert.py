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
Tests to ensure stratis is working as installed from packages.  All
interaction with Stratis will be done through command line.
"""
import argparse
import os
import sys
import time
import unittest
from subprocess import Popen, PIPE

from testlib.utils import exec_command, rpm_package_version, process_exists, \
    file_create, file_signature, rs, stratis_link
from testlib.stratis import StratisCli, STRATIS_CLI, fs_n, p_n

DISKS = []


class StratisCertify(unittest.TestCase):
    """
    Unit tests for Stratis
    """

    def setUp(self):
        """
        Ensure we are ready, which includes stratisd process is up and running
        and we have an empty configuration.  If not we will attempt to make
        the configuration empty.
        :return: None
        """
        self.addCleanup(self._clean_up)

        # The daemon should already be running, if not lets starts it and wait
        # a bit
        if process_exists('stratisd') is None:
            exec_command(["systemctl", "start", "stratisd"])
            time.sleep(20)

        StratisCli.destroy_all()
        self.assertEqual(0, len(StratisCli.pool_list()))

    def _clean_up(self):
        """
        If an exception in raised in setUp, tearDown will not be called, thus
        we will place our cleanup in a method which is called after tearDown
        :return: None
        """
        StratisCli.destroy_all()
        self.assertEqual(0, len(StratisCli.pool_list()))

    @unittest.expectedFailure
    def test_client_version(self):
        """
        Ref. https://bugzilla.redhat.com/show_bug.cgi?id=1652124
        :return: None
        """
        self.assertEqual(
            rpm_package_version('stratis-cli'), StratisCli.cli_version())

    def test_service_version(self):
        """
        Ensure package and version reported from CLI match.
        :return: None
        """
        self.assertEqual(
            rpm_package_version("stratisd"), StratisCli.daemon_version())

    def test_daemon_redundancy(self):
        """
        Test daemon redundancy returns expected values.
        :return:
        """
        self.assertEqual(("NONE", 0), StratisCli.daemon_redundancy())

    def test_pool_create(self):
        """
        Test pool create.
        :return: None
        """
        pool_name = p_n()
        StratisCli.pool_create(pool_name, [DISKS[0]])
        pools = StratisCli.pool_list()
        self.assertTrue(pool_name in pools)
        self.assertEqual(1, len(pools))

    def test_pool_rename(self):
        """
        Test pool rename
        :return:
        """
        pool_name = p_n()
        new_name = p_n()
        StratisCli.pool_create(pool_name, [DISKS[0]])
        self.assertTrue(pool_name in StratisCli.pool_list())
        StratisCli.pool_rename(pool_name, new_name)
        pl = StratisCli.pool_list()
        self.assertEqual(len(pl), 1)
        self.assertTrue(new_name in pl)

    def test_pool_destroy(self):
        """
        Test destroying a pool
        :return: None
        """
        pool_name = p_n()
        StratisCli.pool_create(pool_name, [DISKS[0]])
        StratisCli.pool_destroy(pool_name)
        pools = StratisCli.pool_list()
        self.assertFalse(pool_name in pools)
        self.assertEqual(0, len(pools))

    def test_pool_add_data(self):
        """
        Test adding a data device to a pool.
        :return: None
        """
        pool_name = p_n()
        StratisCli.pool_create(pool_name, [DISKS[0]])
        StratisCli.pool_add(pool_name, "add-data", DISKS[1:])
        block_devs = StratisCli.blockdev_list()

        for d in DISKS:
            self.assertTrue(d in block_devs)

    def test_pool_add_cache(self):
        """
        Test adding cache to a pool
        :return: None
        """
        pool_name = p_n()
        StratisCli.pool_create(pool_name, [DISKS[0]])
        StratisCli.pool_add(pool_name, "add-cache", DISKS[1:])
        block_devs = StratisCli.blockdev_list()

        for d in DISKS:
            self.assertTrue(d in block_devs)

    def test_fs_create(self):
        """
        Test creating a FS
        :return: None
        """
        pool_name = p_n()
        fs_name = fs_n()
        StratisCli.pool_create(pool_name, [DISKS[0]])
        StratisCli.fs_create(pool_name, fs_name)
        fs = StratisCli.fs_list()
        self.assertTrue(fs_name in fs.keys())
        self.assertEqual(1, len(fs))
        self.assertEqual(fs[fs_name]["POOL_NAME"], pool_name)

    def test_fs_destroy(self):
        """
        Test destroying a FS
        :return:
        """
        pool_name = p_n()
        fs_name = fs_n()
        fs_too = fs_n()
        StratisCli.pool_create(pool_name, [DISKS[0]])
        StratisCli.fs_create(pool_name, fs_name)
        StratisCli.fs_create(pool_name, fs_too)
        StratisCli.fs_destroy(pool_name, fs_name)

        fs = StratisCli.fs_list()
        self.assertEqual(1, len(fs))
        self.assertFalse(fs_n in fs)
        self.assertTrue(fs_too in fs)

    def test_fs_snap_shot(self):
        """
        Test creating a FS snap shot.
        :return: None
        """
        pool_name = p_n()
        fs_name = fs_n()
        fs_ss = fs_n()
        StratisCli.pool_create(pool_name, [DISKS[0]])
        StratisCli.fs_create(pool_name, fs_name)
        StratisCli.fs_ss_create(pool_name, fs_name, fs_ss)
        fs = StratisCli.fs_list()
        self.assertTrue(fs_ss in fs)

    def test_block_dev_list(self):
        """
        Test block device listing
        :return:
        """
        pool_name = p_n()
        StratisCli.pool_create(pool_name, [DISKS[0]])

        block_devs = StratisCli.blockdev_list()
        self.assertTrue(DISKS[0] in block_devs)
        self.assertEqual(1, len(block_devs))
        self.assertEqual(pool_name, block_devs[DISKS[0]]["POOL_NAME"])

    @unittest.expectedFailure
    def test_no_args(self):
        """
        Ref. https://github.com/stratis-storage/stratis-cli/issues/248
        :return: None
        """
        exec_command([STRATIS_CLI], 2)
        exec_command([STRATIS_CLI, "daemon"], 2)

    def test_fs_rename(self):
        """
        Test renaming a FS
        :return: None
        """
        pool_name = p_n()
        fs_name = fs_n()
        fs_new_name = fs_n()
        StratisCli.pool_create(pool_name, [DISKS[0]])
        StratisCli.fs_create(pool_name, fs_name)
        StratisCli.fs_rename(pool_name, fs_name, fs_new_name)

        fs = StratisCli.fs_list()
        self.assertTrue(fs_new_name in fs.keys())
        self.assertFalse(fs_name in fs.keys())
        self.assertEqual(1, len(fs))

    @unittest.expectedFailure
    def test_signal_interruption(self):
        """
        Send a signal in the middle of a command to ensure that we don't get
        a stack trace, ref. https://bugzilla.redhat.com/show_bug.cgi?id=1686652
        :return:
        """
        process = Popen(
            [STRATIS_CLI, "pool", "create",
             p_n(), DISKS[0]],
            stdout=PIPE,
            stderr=PIPE,
            close_fds=True,
            env=os.environ)
        time.sleep(0.05)
        process.send_signal(2)
        result = process.communicate()
        stdout_text = ""
        stderr_text = ""
        if result[0]:
            stdout_text = bytes(result[0]).decode("utf-8")
        if result[1]:
            stderr_text = bytes(result[1]).decode("utf-8")

        self.assertTrue("Traceback" not in stdout_text)
        self.assertTrue("Traceback" not in stderr_text)
        self.assertNotEqual(process.returncode, 0)

    def test_no_list_listings(self):
        """
        Test that commands that optionally take a list work both ways.
        :return: None
        """
        pool_name = p_n()
        fs_name = fs_n()
        StratisCli.pool_create(pool_name, block_devices=DISKS)
        StratisCli.fs_create(pool_name, fs_name)

        self.assertEqual(StratisCli.pool_list(), StratisCli.pool_list(False))
        self.assertEqual(StratisCli.fs_list(), StratisCli.fs_list(False))
        self.assertEqual(StratisCli.blockdev_list(),
                         StratisCli.blockdev_list(False))

    def test_simple_data_io(self):
        """
        Create a pool and fs, create some files on it and validate them to
        ensure very basic data path is working.
        :return: None
        """
        mount_path = None
        try:
            pool_name = p_n()
            fs_name = fs_n()
            StratisCli.pool_create(pool_name, block_devices=DISKS)
            StratisCli.fs_create(pool_name, fs_name)

            # mount the fs
            mount_path = os.path.join(os.path.sep + "mnt", rs(16))
            os.mkdir(mount_path)
            exec_command(
                ["mount",
                 stratis_link(pool_name, fs_name), mount_path])

            files = {}
            total_size = 0
            # Do some simple IO to it, creating at most about ~100MiB data
            while total_size < 1024 * 1024 * 100:
                fn, signature, size = file_create(mount_path)
                total_size += size
                files[fn] = signature

            # Validate them
            for name, signature in files.items():
                self.assertTrue(file_signature(name), signature)

        finally:
            # Make sure we un-mount the fs before we bail as we can't clean up
            # Stratis when the FS is mounted.
            if mount_path:
                exec_command(["umount", mount_path])
                os.rmdir(mount_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--disk",
        action="append",
        dest="DISKS",
        help="disks to use",
        required=True)
    disks, args = ap.parse_known_args()
    DISKS = disks.DISKS
    print("Using block device(s) for tests: %s" % DISKS)
    unittest.main(argv=sys.argv[:1] + args)
