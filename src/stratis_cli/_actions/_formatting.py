# Copyright 2016 Red Hat, Inc.
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
Formatting for tables.
"""

import sys


def print_table(column_headings, row_entries, alignment, file=sys.stdout):
    """
    Given the column headings and the row_entries, print a table.
    Align according to alignment specification and always pad with 2 spaces.

    :param column_headings: the column headings
    :type column_headings: list of str
    :param row_entries: a list of the row entries
    :type row_entries: list of list of str
    :param alignment: the alignment indicator for each key, '<', '>', '^', '='
    :type alignment: list of str

    Precondition: len(column_headings) == len(alignment) == len of each entry
    in row_entries.
    """

    num_columns = len(column_headings)

    column_lengths = [
        max(
            max((len(e[index]) for e in row_entries), default=0),
            len(column_headings[index])) + 2 for index in range(num_columns)
    ]

    for index in range(num_columns):
        line = '{0:{align}{width}}'.format(
            column_headings[index],
            align=alignment[index],
            width=column_lengths[index])
        print(line, end='', file=file)
    print(file=file)

    for row in row_entries:
        for index in range(num_columns):
            line = '{0:{align}{width}}'.format(
                row[index],
                align=alignment[index],
                width=column_lengths[index])
            print(line, end='', file=file)
        print(file=file)
