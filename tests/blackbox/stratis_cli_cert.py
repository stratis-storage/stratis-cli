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

from testlib.utils import exec_command, process_exists
from testlib.stratis import StratisCli

DISKS = []


def _clean_up():
    """
    Try to clean up after a test failure.

    :return: None
    """
    StratisCli.destroy_all()
    assert StratisCli.pool_list() == []


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
        self.addCleanup(_clean_up)

        if process_exists("stratisd") is None:
            exec_command(["systemctl", "start", "stratisd"])
            time.sleep(20)

        StratisCli.destroy_all()
        assert StratisCli.pool_list() == []


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--disk", action="append", dest="DISKS", help="disks to use", required=True
    )
    disks, args = ap.parse_known_args()
    DISKS = disks.DISKS
    print("Using block device(s) for tests: %s" % DISKS)
    unittest.main(argv=sys.argv[:1] + args)
