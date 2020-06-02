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
Test error type string formatting.
"""

# isort: STDLIB
import unittest

# isort: LOCAL
from stratis_cli._errors import (
    StratisCliAggregateError,
    StratisCliEngineError,
    StratisCliEnginePropertyError,
    StratisCliGenerationError,
    StratisCliIncoherenceError,
    StratisCliPropertyNotFoundError,
    StratisCliUnknownInterfaceError,
)


class ErrorFmtTestCase(unittest.TestCase):
    """
    Test stringification of various error types.
    """

    def _string_not_empty(self, exception):
        """
        :param exception: an object of a Stratis CLI error type
        :type exception: Exception
        """
        self.assertNotEqual(str(exception), "")

    def test_stratis_cli_property_not_found_error_fmt(self):
        """
        Test 'StratisCliPropertyNotFoundError'
        """
        self._string_not_empty(StratisCliPropertyNotFoundError("BadProperty"))

    def test_stratis_cli_incoherence_error_fmt(self):
        """
        Test 'StratisCliIncoherenceError'
        """
        self._string_not_empty(StratisCliIncoherenceError("Error"))

    def test_stratis_cli_unknown_interface_error_fmt(self):
        """
        Test 'StratisCliUnknownInterfaceError'
        """
        self._string_not_empty(StratisCliUnknownInterfaceError("BadInterface"))

    def test_stratis_cli_generation_error_fmt(self):
        """
        Test 'StratisCliGenerationError'
        """
        self._string_not_empty(StratisCliGenerationError("Error"))

    def test_stratis_cli_engine_property_error_fmt(self):
        """
        Test 'StratisCliEnginePropertyError'
        """
        self._string_not_empty(StratisCliEnginePropertyError("name", "whoops"))

    def test_stratis_cli_aggregate_error_fmt(self):
        """
        Test 'StratisCliAggregateError'
        """
        self._string_not_empty(
            StratisCliAggregateError(
                "do lots of things", "toy", [StratisCliEngineError(1, "bad")]
            )
        )
