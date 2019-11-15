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
Test formatting.
"""

import filecmp
import os
import unittest

from stratis_cli._actions._formatting import print_table


class FormattingTestCase(unittest.TestCase):
    """
    Test formatting.
    """

    def testPrintTable(self):
        """
        Test printing a table
        """

        expected_output = open("expected_output.txt", "w+")
        expected_output.write(
            """Pool Name    Name  Used     Created            Device\n
yes_you_can  ☺     546 MiB  Oct 05 2018 16:24  /dev/stratis/yes_you_can/☺\n
yes_you_can  漢字    546 MiB  Oct 10 2018 09:37  /dev/stratis/yes_you_can/漢字"""
        )

        actual_output = open("actual_output.txt", "w+")

        table = [
            ["Pool Name", "Name", "Used", "Created", "Device"],
            [
                "yes_you_can",
                "☺",
                "546 MiB",
                "Oct 05 2018 16:24",
                "/dev/stratis/yes_you_can/☺",
            ],
            [
                "yes_you_can",
                "漢字",
                "546 MiB",
                "Oct 10 2018 09:37",
                "/dev/stratis/yes_you_can/漢字",
            ],
        ]

        print_table(table[0], table[1:], ["<", "<", "<", "<", "<"], actual_output)

        self.assertEqual(filecmp.cmp("expected_output.txt", "actual_output.txt"), True)

        expected_output.close()
        actual_output.close()

        os.remove("expected_output.txt")
        os.remove("actual_output.txt")
