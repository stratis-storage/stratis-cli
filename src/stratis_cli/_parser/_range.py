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

# isort: THIRDPARTY
from justbytes import ROUND_DOWN, B, GiB, KiB, MiB, Range, RangeValueError, TiB


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
    raise RuntimeError('Unknown unit specifier "%s"' % unit_specifier)


class RangeAction(argparse.Action):
    """
    Parse a justbytes Range from a str

    Round down to the nearest byte
    """

    # pylint: disable=redefined-builtin
    def __init__(self, option_strings, dest, **kwargs):
        """
        Initialize the object
        """
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Set dest namespace attribute to Range value parsed from values.
        """
        parts = values.split(" ", 1)
        try:
            (magnitude, unit) = (parts[0], parts[1])
        except IndexError as err:
            raise argparse.ArgumentError(
                self, "Space required between magnitude and unit specifier"
            ) from err

        try:
            units = _unit_map(unit)
        except RuntimeError as err:
            raise argparse.ArgumentError(self, str(err)) from err

        try:
            size = Range(magnitude, units).roundTo(B, rounding=ROUND_DOWN)
        except RangeValueError as err:
            raise argparse.ArgumentError(self, str(err)) from err

        setattr(namespace, self.dest, size)
