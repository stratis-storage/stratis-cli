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

# isort: THIRDPARTY
from wcwidth import wcswidth

# isort: LOCAL
from stratis_cli._actions._formatting import print_table


# pylint: disable=fixme
# TODO: Use Hypothesis library to create numerous test inputs.
class FormattingTestCase1(unittest.TestCase):
    """
    Test formatting.
    """

    def setUp(self):
        self.output = io.StringIO()

        self.table = [
            ["Pool Na\u030ame", "Na\u030ame", "Used", "Created", "Device", "UUID"],
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
                "☺",
                "546 MiB",
                "Feb 07 2019 15:33",
                "/stratis/unicode/☺",
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
                "漢字",
                "546 MiB",
                "Feb 07 2019 15:33",
                "/stratis/unicodé/漢字",
                "4ecacb15fb64453191d7da731c5f1601",
            ],
        ]
        print_table(
            self.table[0], self.table[1:], ["<", "<", "<", "<", "<", "<"], self.output
        )

    def test_contains_equally_long_rows(self):
        """
        Test that the table's rows are of equal length
        """
        self.output.seek(0)
        row_lengths = map(wcswidth, self.output.readlines())
        self.assertEqual(len(frozenset(row_lengths)), 1)

    def test_contains_correct_number_of_lines(self):
        """
        Test that the table contains the correct number of lines
        """
        self.output.seek(0)
        self.assertEqual(len(self.output.readlines()), len(self.table))
