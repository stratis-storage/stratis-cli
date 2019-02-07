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

from wcwidth import wcswidth


def _get_column_width_chars(column_width_cells, entry):
    """
    From the desired column width in cells and the item to be printed,
    calculate the required column width in characters to pass to the
    format method.

    In order to get the correct width in chars it is necessary to subtract
    the number of cells above 1 (or add the number of cells below 1) that
    an individual character occupies.

    :param int column_width_cells: the column width, in cells
    :param str entry: the entry to be printed

    :returns: the column width in characters

    Precondition: mcswidth(entry) != -1
                  (equivalently, entry has no unprintable characters)
    """
    return column_width_cells - (wcswidth(entry) - len(entry))


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

    Precondition: all(mcswidth(h) != -1 for h in column_headings)
                  all(mcswidth(i) != -1 for row in rows for item in row)
                  (in other words, no items to be printed contain
                   unprintable characters)
    """

    num_columns = len(column_headings)

    column_lengths = [
        max(
            max((wcswidth(e[index]) for e in row_entries), default=0),
            wcswidth(column_headings[index])) + 2
        for index in range(num_columns)
    ]

    for index in range(num_columns):
        entry = column_headings[index]
        column_width_chars = _get_column_width_chars(column_lengths[index],
                                                     entry)
        line = '{0:{align}{width}}'.format(
            entry, align=alignment[index], width=column_width_chars)
        print(line, end='', file=file)
    print(file=file)

    for row in row_entries:
        for index in range(num_columns):
            entry = row[index]
            column_width_chars = _get_column_width_chars(
                column_lengths[index], entry)

            line = '{0:{align}{width}}'.format(
                entry, align=alignment[index], width=column_width_chars)
            print(line, end='', file=file)
        print(file=file)
