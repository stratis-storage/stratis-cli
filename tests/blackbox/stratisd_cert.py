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

from testlib.utils import exec_command, exec_test_command, process_exists
from testlib.dbus import StratisDbus, clean_up

DISKS = []


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


if __name__ == "__main__":
    ARGUMENT_PARSER = argparse.ArgumentParser()
    ARGUMENT_PARSER.add_argument(
        "--disk", action="append", dest="DISKS", help="disks to use", required=True
    )
    PARSED_ARGS, OTHER_ARGS = ARGUMENT_PARSER.parse_known_args()
    DISKS = PARSED_ARGS.DISKS
    print("Using block device(s) for tests: %s" % DISKS)
    unittest.main(argv=sys.argv[:1] + OTHER_ARGS)
