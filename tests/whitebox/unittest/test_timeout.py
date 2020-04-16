# Copyright 2019 Red Hat, Inc.
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

# isort: STDLIB
import unittest

# isort: LOCAL
from stratis_cli import StratisCliEnvironmentError
from stratis_cli._actions._timeout import get_timeout


class TimeoutTestCase(unittest.TestCase):
    """
    Test various timeout inputs.
    """

    def test_timout_too_large(self):
        """
        Should fail because the timeout value is too large.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            get_timeout("1073741824")

    def test_timout_too_large_int(self):
        """
        Should fail because the timeout value is too large.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            get_timeout(1073741824)

    def test_timout_too_small_str(self):
        """
        Should fail because the timeout value is too small.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            get_timeout("-2")

    def test_timout_too_small_int(self):
        """
        Should fail because the timeout value is too small.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            get_timeout(-2)

    def test_timout_float_str(self):
        """
        Should fail because the timeout value is a float.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            get_timeout("2.0")

    def test_timout_float_float(self):
        """
        Should fail because the timeout value is a float.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            get_timeout(2.0)

    def test_timout_not_int(self):
        """
        Should fail because the timeout value is not an integer.
        """
        with self.assertRaises(StratisCliEnvironmentError):
            get_timeout("hello")

    def test_timout_correct_return_value_str_1000(self):
        """
        An input value of "1000" should return 1.0.
        """
        self.assertEqual(get_timeout("1000"), 1.0)

    def test_timout_correct_return_value_int_1000(self):
        """
        An input value of 1000 should return 1.0.
        """
        self.assertEqual(get_timeout(1000), 1.0)

    def test_timout_correct_return_value_str_0(self):
        """
        An input value of "0" should return 0.
        """
        self.assertEqual(get_timeout("0"), 0)

    def test_timout_correct_return_value_int_0(self):
        """
        An input value of 0 should return 0.
        """
        self.assertEqual(get_timeout(0), 0)
