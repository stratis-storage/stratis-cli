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
Test properties of range parsing.
"""

# isort: STDLIB
import unittest

# isort: THIRDPARTY
import justbytes

# isort: LOCAL
from stratis_cli._parser._range import _unit_map


class TestUnitMap(unittest.TestCase):
    """
    Test that _unit_map maps input string to the correct units.
    """

    def test_all_units(self):
        """
        Test that _unit_map maps to correct units
        """
        self.assertEqual(_unit_map("B"), justbytes.B)
        self.assertEqual(_unit_map("KiB"), justbytes.KiB)
        self.assertEqual(_unit_map("MiB"), justbytes.MiB)
        self.assertEqual(_unit_map("GiB"), justbytes.GiB)
        self.assertEqual(_unit_map("TiB"), justbytes.TiB)
        self.assertEqual(_unit_map("PiB"), justbytes.PiB)

    def test_not_units(self):
        """
        Test that an AssertionError is raised on a bogus unit string.
        """
        with self.assertRaises(AssertionError):
            _unit_map("WiB")
