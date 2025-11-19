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
Test 'constants'.
"""

# isort: STDLIB
import os
import unittest

# isort: LOCAL
from stratis_cli._actions._utils import PoolFeature
from stratis_cli._alerts import PoolAlert
from stratis_cli._constants import FilesystemId, IdType


class PoolAlertTestCase(unittest.TestCase):
    """
    Tests for PoolAlert methods.
    """

    def test_parsing_bogus_str(self):
        """
        Test parsing a string that does not correspond to any value.
        """
        self.assertIsNone(PoolAlert.from_str("bogus"))

    def test_parsing_all_non_bogus_str(self):
        """
        Just generate all non bogus strings and parse them.
        """
        for code in PoolAlert.codes():
            self.assertEqual(PoolAlert.from_str(str(code)), code)

    def test_summarize(self):
        """
        Verify valid strings returned from summarize() method.
        """
        for code in PoolAlert.codes():
            summary_value = code.summarize()
            self.assertIsInstance(summary_value, str)
            self.assertNotEqual(summary_value, "")


class FilesystemIdTestCase(unittest.TestCase):
    """
    Unit tests for FilesystemId.
    """

    def test_str_method(self):
        """
        Just exercise the __str__ method.
        """
        self.assertTrue("filesystem" in str(FilesystemId(IdType.NAME, "name")))


class PoolFeatureTestCase(unittest.TestCase):
    """
    Unit test for PoolFeature
    """

    def test_str_method(self):
        """
        Test __str__ method's result and parsing.
        """

        for feature in PoolFeature:
            if feature is PoolFeature.UNRECOGNIZED:
                self.assertIsInstance(str(feature), str)
                if bool(int(os.environ.get("STRATIS_STRICT_POOL_FEATURES", False))):
                    with self.assertRaises(ValueError):
                        PoolFeature("unknown")
            else:
                self.assertEqual(str(feature), feature.value)
                self.assertEqual(PoolFeature(feature.value), feature)

    def test_many_types_missing(self):
        """
        Test the _missing_ method by passing many types of argument. This is
        mostly to help monkeytype realize that the type of _missing_'s
        value parameter is not just str.
        """
        if bool(int(os.environ.get("STRATIS_STRICT_POOL_FEATURES", 0))):

            def test_func(val):
                self.assertIsNone(
                    PoolFeature._missing_(val)  # pylint: disable=protected-access
                )

        else:

            def test_func(val):
                self.assertEqual(
                    PoolFeature._missing_(val),  # pylint: disable=protected-access
                    PoolFeature.UNRECOGNIZED,
                )

        for val in [1, 0.347, ["a"], {"b": 32}, lambda x: 32]:
            with self.subTest(val=val):
                test_func(val)
