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
        test_value = "2147483648"

        try:
            get_timeout(test_value)
        except StratisCliEnvironmentError as e:
            self.assertIsInstance(e, StratisCliEnvironmentError)

    def testTimeoutTooSmall(self):
        """
        Should fail because the timeout value is too small.
        """
        test_value = "-2"

        try:
            get_timeout(test_value)
        except StratisCliEnvironmentError as e:
            self.assertIsInstance(e, StratisCliEnvironmentError)

    def testTimeoutNotInteger(self):
        """
        Should fail because the timeout value is not an integer.
        """
        test_value = "hello"

        try:
            get_timeout(test_value)
        except StratisCliEnvironmentError as e:
            self.assertIsInstance(e, StratisCliEnvironmentError)

    def testTimeoutFloat(self):
        """
        Should fail because the timeout value is a float.
        """
        test_value = "2.0"

        try:
            get_timeout(test_value)
        except StratisCliEnvironmentError as e:
            self.assertIsInstance(e, StratisCliEnvironmentError)
