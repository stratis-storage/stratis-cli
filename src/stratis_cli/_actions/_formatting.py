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

# isort: STDLIB
import sys

from .._errors import StratisCliPropertyNotFoundError

# If the wcwidth package is not available the wcswidth function will not
# be available. In that case, use the standard function len where wcswidth
# would otherwise be used. Since len determines the number of _characters_
# in a string, rather than its width in cells, text containing characters
# occupying more or less than one cell, will in the general case, not be
# properly aligned in the column output. The wcwidth package may not be
# available in every distribution due to the non-local nature of its
# installation mechanism, which builds functions dynamically from tables
# made available online at www.unicode.org.

# Disable coverage for conditional import. We do not want to make our
# coverage result dependent on whether wcwidth is available or not, as our
# tests might be run, and succeed either with or without.
try:
    from wcwidth import wcswidth

    maybe_wcswidth = wcswidth  # pragma: no cover

except ImportError:  # pragma: no cover
    maybe_wcswidth = len

# placeholder for tables where a desired value was not obtained from stratisd
# when the value should be supported.
TABLE_FAILURE_STRING = "FAILURE"


def fetch_property(object_type, props, name, to_repr):
    """
    Get a representation of a property fetched through FetchProperties interface

    :param object_type: string representation of object type implementing FetchProperties
    :type object_type: str
    :param props: dictionary of property names mapped to values
    :type props: dict of strs to (bool, object)
    :param name: the name of the property
    :type name: str
    :param to_repr: function expecting one object argument to convert to some type
    :type to_repr: function(object) -> object
    :returns: object produced by to_repr or None
    :raises StratisCliPropertyNotFoundError:
    """
    # Disable coverage for failure of the engine to successfully get a value
    # or for a property not existing for a specified key. We can not force the
    # engine error easily and should not force it these CLI tests. A KeyError
    # can only be raised if there is a bug in the code or if the version of
    # stratisd being run is not compatible with the version of the CLI being
    # tested. We expect to avoid those conditions, and choose not to test for
    # them.
    try:
        (success, variant) = props[name]
        if not success:
            return None  # pragma: no cover
        return to_repr(variant)
    except KeyError:  # pragma: no cover
        raise StratisCliPropertyNotFoundError(object_type, name)


def _get_column_len(column_width, entry_len, entry_width):
    """
    From the desired column width in cells and the item to be printed,
    calculate the required number of characters to pass to the format method.

    In order to get the correct width in chars it is necessary to subtract
    the number of cells above 1 (or add the number of cells below 1) that
    an individual character occupies.

    :param int column_width: the column width, in cells
    :param int entry_len: the entry len, in characters
    :param int entry_width: the entry width, in cells

    :returns: the column width in characters

    Note that if wcswidth has defaulted to len,
    entry_width == entry_len, so the result is always column_width.

    Precondition: entry_width != -1
                  (equivalently, entry has no unprintable characters)
    """
    return column_width - (entry_width - entry_len)


def _print_row(file, row, row_widths, column_widths, column_alignments):
    """
    Print a single row in a table. The row might be the header row, or
    a row of data items.

    :param file: file to print to
    :param list row: the list of items to print
    :param list row_widths: the list of wcswidth for the row
    :param list column_widths: corresponding list of column widths
    :param list column_alignments: corresponding list of column alignment specs

    Precondition: len(row) == len(column_widths) == len(alignment)
    Precondition: no elements of row have unprintable characters
    """
    entries = []
    for index, entry in enumerate(row):
        column_len = _get_column_len(
            column_widths[index], len(entry), row_widths[index]
        )
        entries.append(
            "{0:{align}{width}}".format(
                entry, align=column_alignments[index], width=column_len
            )
        )
    print("  ".join(entries), end="", file=file)


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
                  (i.e., no items to be printed contain unprintable characters)
    """
    column_widths = [0] * len(column_headings)
    cell_widths = []

    # Column header isn't different than any other row, insert into rows.
    row_entries.insert(0, column_headings)

    for row_index, row in enumerate(row_entries):
        cell_widths.append([])
        for column_index, cell in enumerate(row):
            cell_width = maybe_wcswidth(cell)
            cell_widths[row_index].append(cell_width)
            column_widths[column_index] = max(column_widths[column_index], cell_width)

    for row, row_widths in zip(row_entries, cell_widths):
        _print_row(file, row, row_widths, column_widths, alignment)
        print(file=file)


def main():  # pragma: no cover
    """
    A function that prints out some tables.
    To be used for a visual check of correctness of formatting.
    """

    print("Example table...")
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
    print_table(table[0], table[1:], ["<", "<", "<", "<", "<"])

    print()
    print("Example table...")
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
    print_table(table[0], table[1:], ["<", "<", "<", "<", "<", "<"])


if __name__ == "__main__":  # pragma: no cover
    main()
