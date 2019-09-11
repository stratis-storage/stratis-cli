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
Test 'timeout'.
"""

import unittest

from stratis_cli._errors import StratisCliEnvironmentError
from stratis_cli._actions._data import _get_timeout


class TimeoutTestCase(unittest.TestCase):
    """
    Test various timeout inputs.
    """

    def testTimeoutTooLarge(self):
        """
        Should fail because the timeout value is too large.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            _get_timeout("1073741824")

    def testTimeoutTooLargeInt(self):
        """
        Should fail because the timeout value is too large.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            _get_timeout(1073741824)

    def testTimeoutTooSmallStr(self):
        """
        Should fail because the timeout value is too small.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            _get_timeout("-2")

    def testTimeoutTooSmallInt(self):
        """
        Should fail because the timeout value is too small.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            _get_timeout(-2)

    def testTimeoutFloatStr(self):
        """
        Should fail because the timeout value is a float.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            _get_timeout("2.0")

    def testTimeoutFloatFloat(self):
        """
        Should fail because the timeout value is a float.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            _get_timeout(2.0)

    def testTimeoutNotInt(self):
        """
        Should fail because the timeout value is not an integer.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            _get_timeout("hello")

    def testTimeoutCorrectReturnValueStr1000(self):
        """
        An input value of "1000" should return 1.0.
        """
        self.assertEqual(_get_timeout("1000"), 1.0)

    def testTimeoutCorrectReturnValueInt1000(self):
        """
        An input value of 1000 should return 1.0.
        """
        self.assertEqual(_get_timeout(1000), 1.0)

    def testTimeoutCorrectReturnValueStr0(self):
        """
        An input value of "0" should return 0.
        """
        self.assertEqual(_get_timeout("0"), 0)

    def testTimeoutCorrectReturnValueInt0(self):
        """
        An input value of 0 should return 0.
        """
        self.assertEqual(_get_timeout(0), 0)
