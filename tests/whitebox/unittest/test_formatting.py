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

# isort: STDLIB
import io
import unittest

# isort: LOCAL
from stratis_cli._actions._formatting import print_table


class FormattingTestCase(unittest.TestCase):
    """
    Test formatting.
    """

    def setUp(self):
        self.output = io.StringIO()

        # pylint: disable=bad-continuation
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
        print_table(table[0], table[1:], ["<", "<", "<", "<", "<"], self.output)

    def testContainsNewLine(self):
        """
        Test that the table contains a new line
        """
        self.assertRegex(self.output.getvalue(), "\n")

    def testContainsCorrectNumberOfLines(self):
        """
        Test that the table contains the correct number of lines
        """
        self.output.seek(0)
        self.assertEqual(len(self.output.readlines()), 3)


class FormattingTestCase2(unittest.TestCase):
    """
    Test formatting.
    """

    def setUp(self):
        self.output = io.StringIO()

        # pylint: disable=bad-continuation
        table = [
            [u"Pool Na\u030ame", u"Na\u030ame", "Used", "Created", "Device", "UUID"],
            [
                "unicode",
                "e",
                "546 MiB",
                "Feb 07 2019 15:33",
                "/stratis/unicode/e",
                "3bf22806a6df4660aa527d646209595f",
            ],
            [
                "unicode",
                "eeee",
                "546 MiB",
                "Feb 07 2019 15:33",
                "/stratis/unicode/eeee",
                "17101e39e72e423c90d8be5cb37c055b",
            ],
            [
                "unicodé",
                "é",
                "546 MiB",
                "Feb 07 2019 15:33",
                "/stratis/unicodé/é",
                "0c2caf641dde41beb40bed6911f75c74",
            ],
            [
                "unicodé",
                "éééé",
                "546 MiB",
                "Feb 07 2019 15:33",
                "/stratis/unicodé/éééé",
                "4ecacb15fb64453191d7da731c5f1601",
            ],
        ]
        print_table(table[0], table[1:], ["<", "<", "<", "<", "<", "<"], self.output)

    def testContainsNewLine(self):
        """
        Test that the table contains a new line
        """
        self.assertRegex(self.output.getvalue(), "\n")

    def testContainsCorrectNumberOfLines(self):
        """
        Test that the table contains the correct number of lines
        """
        self.output.seek(0)
        self.assertEqual(len(self.output.readlines()), 5)
