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
import unittest

# isort: LOCAL
from stratis_cli._actions._utils import PoolFeature
from stratis_cli._constants import FilesystemId, IdType
from stratis_cli._error_codes import (
    PoolAllocSpaceErrorCode,
    PoolErrorCode,
    PoolMaintenanceErrorCode,
)


class PoolMaintenanceErrorCodeTestCase(unittest.TestCase):
    """
    Test properties of PoolMaintenanceErrorCode
    """

    def test_parsing_str(self):
        """
        Parsing a known string returns the correct value.
        """
        for item in list(PoolMaintenanceErrorCode):
            self.assertEqual(PoolMaintenanceErrorCode.from_str(str(item)), item)

    def test_parsing_bogus_str(self):
        """
        Parsing a string that does not correspond to any value returns None.
        """
        self.assertIsNone(PoolMaintenanceErrorCode.from_str("totally super"))


class PoolAllocSpaceErrorCodeTestCase(unittest.TestCase):
    """
    Tests for PoolAllocSpaceErrorCode methods.
    """

    def test_parsing_bogus_str(self):
        """
        Parsing a string that does not correspond to any value returns None.
        """
        self.assertIsNone(PoolAllocSpaceErrorCode.from_str("totally super"))


class PoolErrorCodeTestCase(unittest.TestCase):
    """
    Tests for PoolErrorCode methods.
    """

    def test_parsing_bogus_str(self):
        """
        Test parsing a string that does not correspond to any value.
        """
        with self.assertRaises(StopIteration):
            PoolErrorCode.error_from_str("bogus")


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
        Just exercise the __str__ method
        """

        for feature in PoolFeature:
            self.assertEqual(str(feature), feature.value)
