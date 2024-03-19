# Copyright 2021 Red Hat, Inc.
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
Definition of filesystem actions to display in the CLI.
"""

# isort: STDLIB
import argparse
import re

# isort: THIRDPARTY
from justbytes import B, GiB, KiB, MiB, PiB, Range, TiB

_RANGE_RE = re.compile(r"^(?P<magnitude>[0-9]+)(?P<units>([KMGTP]i)?B)$")

_SIZE_SPECIFICATION = (
    "Size must be specified using the format <magnitude><units> where "
    "<magnitude> is a decimal integer value and <units> is any binary "
    'unit specifier in the set "B", "KiB", "MiB", "GiB", "TiB", '
    'and "PiB".'
)


def _unit_map(unit_specifier):
    """
    A simple function that maps a unit_specifier string
    call to a justbytes unit designation.

    :param str unit_specifier: the string
    :returns: the corresponding justbytes units
    :rtype: justbytes.BinaryUnit
    """
    if unit_specifier == "B":
        return B
    if unit_specifier == "KiB":
        return KiB
    if unit_specifier == "MiB":
        return MiB
    if unit_specifier == "GiB":
        return GiB
    if unit_specifier == "TiB":
        return TiB
    if unit_specifier == "PiB":
        return PiB
    assert False, f'Unknown unit specifier "{unit_specifier}"'


def _parse_range(self, values):
    match = _RANGE_RE.search(values)
    if match is None:
        raise argparse.ArgumentError(
            self, f"Ill-formed size specification: {_SIZE_SPECIFICATION}"
        )

    (magnitude, unit) = (match.group("magnitude"), match.group("units"))

    units = _unit_map(unit)

    return Range(int(magnitude), units)


class RangeAction(argparse.Action):
    """
    Parse a justbytes Range from a str

    Round down to the nearest byte
    """

    def __init__(self, option_strings, dest, **kwargs):
        """
        Initialize the object
        """
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Set dest namespace attribute to Range value parsed from values.
        """
        setattr(namespace, self.dest, _parse_range(self, values))


class RangeActionOrCurrent(argparse.Action):
    """
    Allow specifying a Range or the value "current". Include the original
    value specified by the user as well as the Range result if the user
    specified a valid range. This is purely useful for error messages,
    so that an error message will contain what the user specified if there
    needs to be reported an idempotency error.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Allow "current" as well as range specifications.
        """
        setattr(
            namespace,
            self.dest,
            (None if values == "current" else _parse_range(self, values), values),
        )
