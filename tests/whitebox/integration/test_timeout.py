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

from stratis_cli._actions._data import get_timeout


class TimeoutTestCase(unittest.TestCase):
    """
    Test various timeout inputs.
    """

    def testTimeoutTooLarge(self):
        """
        Should fail because the timeout value is too large.
        """
        try:
            get_timeout("2147483648")
        except StratisCliEnvironmentError as e:
            self.assertIsInstance(e, StratisCliEnvironmentError)

    def testTimeoutTooLargeInt(self):
        """
        Should fail because the timeout value is too large.
        """
        try:
            get_timeout(2147483648)
        except StratisCliEnvironmentError as e:
            self.assertIsInstance(e, StratisCliEnvironmentError)

    def testTimeoutTooSmallString(self):
        """
        Should fail because the timeout value is too small.
        """
        try:
            get_timeout("-2")
        except StratisCliEnvironmentError as e:
            self.assertIsInstance(e, StratisCliEnvironmentError)

    def testTimeoutTooSmallInt(self):
        """
        Should fail because the timeout value is too small.
        """
        try:
            get_timeout(-2)
        except StratisCliEnvironmentError as e:
            self.assertIsInstance(e, StratisCliEnvironmentError)

    def testTimeoutFloatString(self):
        """
        Should fail because the timeout value is a float.
        """
        try:
            get_timeout("2.0")
        except StratisCliEnvironmentError as e:
            self.assertIsInstance(e, StratisCliEnvironmentError)

    def testTimeoutFloatFloat(self):
        """
        Should fail because the timeout value is a float.
        """
        try:
            get_timeout(2.0)
        except StratisCliEnvironmentError as e:
            self.assertIsInstance(e, StratisCliEnvironmentError)

    def testTimeoutNotInteger(self):
        """
        Should fail because the timeout value is not an integer.
        """
        try:
            get_timeout("hello")
        except StratisCliEnvironmentError as e:
            self.assertIsInstance(e, StratisCliEnvironmentError)

    def testTimeoutCorrectReturnValueString1000(self):
        """
        An input value of "1000" should return 1.0.
        """
        self.assertEqual(get_timeout("1000"), 1.0)

    def testTimeoutCorrectReturnValueInt1000(self):
        """
        An input value of 1000 should return 1.0.
        """
        self.assertEqual(get_timeout(1000), 1.0)

    def testTimeoutCorrectReturnValueString0(self):
        """
        An input value of "0" should return 0.
        """
        self.assertEqual(get_timeout("0"), 0)

    def testTimeoutCorrectReturnValueInt0(self):
        """
        An input value of 0 should return 0.
        """
        self.assertEqual(get_timeout(0), 0)
