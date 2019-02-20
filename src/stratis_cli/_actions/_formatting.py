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

    Precondition: wcswidth(entry) != -1
                  (equivalently, entry has no unprintable characters)
    """
    return column_width_cells - (wcswidth(entry) - len(entry))


def _print_row(file, num_columns, row, column_widths, column_alignments):
    """
    Print a single row in a table. The row might be the header row, or
    a row of data items.

    :param file: file to print to
    :param int num_columns: the number of columns in the table
    :param list row: the list of items to print
    :param list column_widths: corresponding list of column widths
    :param list column_alignments: corresponding list of column alignment specs

    Precondition: num_columns == len(row) == len(column_widths) ==
                  len(alignment)
    Precondition: no elements of row have unprintable characters
    """
    for index in range(num_columns):
        entry = row[index]
        column_width_chars = _get_column_width_chars(column_widths[index],
                                                     entry)
        line = '{0:{align}{width}}'.format(
            entry, align=column_alignments[index], width=column_width_chars)
        print(line, end='', file=file)


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
    :param file: file to print too
    :type file: writeable stream

    Precondition: len(column_headings) == len(alignment) == len of each entry
    in row_entries.

    Precondition: all(wcswidth(h) != -1 for h in column_headings)
                  all(wcswidth(i) != -1 for row in rows for item in row)
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

    _print_row(file, num_columns, column_headings, column_lengths, alignment)
    print(file=file)

    for row in row_entries:
        _print_row(file, num_columns, row, column_lengths, alignment)
        print(file=file)


def main():
    """
    A function that prints out some tables.
    To be used for a visual check of correctness of formatting.
    """

    print("Example table...")
    table = [['Pool Name', 'Name', 'Used', 'Created', 'Device'], [
        'yes_you_can', '☺', '546 MiB', 'Oct 05 2018 16:24',
        '/dev/stratis/yes_you_can/☺'
    ], [
        'yes_you_can', '漢字', '546 MiB', 'Oct 10 2018 09:37',
        '/dev/stratis/yes_you_can/漢字'
    ]]
    print_table(table[0], table[1:], ['<', '<', '<', '<', '<'])

    print()
    print("Example table...")
    table = [['Pool Name', 'Name', 'Used', 'Created', 'Device', 'UUID'], [
        'unicode', 'e', '546 MiB', 'Feb 07 2019 15:33', '/stratis/unicode/e',
        '3bf22806a6df4660aa527d646209595f'
    ], [
        'unicode', 'eeee', '546 MiB', 'Feb 07 2019 15:33',
        '/stratis/unicode/eeee', '17101e39e72e423c90d8be5cb37c055b'
    ], [
        'unicodé', 'é', '546 MiB', 'Feb 07 2019 15:33',
        '/stratis/unicodé/é', '0c2caf641dde41beb40bed6911f75c74'
    ], [
        'unicodé', 'éééé', '546 MiB', 'Feb 07 2019 15:33',
        '/stratis/unicodé/éééé', '4ecacb15fb64453191d7da731c5f1601'
    ]]
    print_table(table[0], table[1:], ['<', '<', '<', '<', '<', '<'])


if __name__ == "__main__":
    main()
