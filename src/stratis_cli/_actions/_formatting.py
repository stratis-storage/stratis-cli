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
import uuid

from .._errors import StratisCliEnginePropertyError, StratisCliPropertyNotFoundError
from ._utils import unpack_property

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
    # isort: THIRDPARTY
    from wcwidth import wcswidth

    MAYBE_WCSWIDTH = wcswidth  # pragma: no cover

except ImportError:  # pragma: no cover
    MAYBE_WCSWIDTH = len

# placeholder for tables where a desired value was not obtained from stratisd
# when the value should be supported.
TABLE_FAILURE_STRING = "FAILURE"


def get_property(props, name, to_repr, default):
    """
    Get a representation of a property fetched through FetchProperties
    :param props: dictionary of property names mapped to values
    :type props: dict of str * (bool, object)
    :param str name: the name of the property
    :param to_repr: function expecting one object argument to convert
    :type to_repr: object -> object
    :param default: object to return in lieu of propagating an exception
    :type default: object
    :returns: object produced by to_repr or default
    :rtype: object
    """
    try:
        return to_repr(unpack_property(props, name))
    # An exception should only be raised if the property can not be obtained.
    # This requires either running against an interface that does not support
    # the property or the engine encountering an error getting the property,
    # or a bug in our code.
    except (
        StratisCliEnginePropertyError,
        StratisCliPropertyNotFoundError,
    ):  # pragma: no cover
        return default


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
    print("   ".join(entries), end="", file=file)


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
            cell_width = MAYBE_WCSWIDTH(cell)
            cell_widths[row_index].append(cell_width)
            column_widths[column_index] = max(column_widths[column_index], cell_width)

    for row, row_widths in zip(row_entries, cell_widths):
        _print_row(file, row, row_widths, column_widths, alignment)
        print(file=file)


def to_hyphenated(mo_uuid):
    """
    Convert uuid string to hyphenated format
    """
    return str(uuid.UUID(mo_uuid))


def total_used_free(total, used):
    """
    Given total and used, calculate free and display in total / used /free
    format.

    :param Range total: total size
    :param Range used: used size

    :rtype: str
    """
    free = None if total is None or used is None else total - used

    return "%s / %s / %s" % (
        TABLE_FAILURE_STRING if total is None else total,
        TABLE_FAILURE_STRING if used is None else used,
        TABLE_FAILURE_STRING if free is None else free,
    )
