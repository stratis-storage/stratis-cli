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

import argparse
import unittest

from stratis_cli._errors import StratisCliError
from stratis_cli._errors import StratisCliRuntimeError
from stratis_cli._errors import StratisCliPropertyNotFoundError
from stratis_cli._errors import StratisCliPartialChangeError
from stratis_cli._errors import StratisCliNoChangeError
from stratis_cli._errors import StratisCliIncoherenceError
from stratis_cli._errors import StratisCliInUseError
from stratis_cli._errors import StratisCliUnknownInterfaceError
from stratis_cli._errors import StratisCliEngineError
from stratis_cli._errors import StratisCliActionError
from stratis_cli._errors import StratisCliGenerationError
from stratis_cli._errors import StratisCliEnvironmentError

from stratis_cli._stratisd_constants import BlockDevTiers


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

    def testStratisCliErrorFmt(self):
        """
        Test 'StratisCliError'
        """
        self._string_not_empty(StratisCliError("Error"))

    def testStratisCliRuntimeErrorFmt(self):
        """
        Test 'StratisCliRuntimeError'
        """
        self._string_not_empty(StratisCliRuntimeError("Error"))

    def testStratisCliPropertyNotFoundErrorFmt(self):
        """
        Test 'StratisCliPropertyNotFoundError'
        """
        self._string_not_empty(
            StratisCliPropertyNotFoundError("BadInterface", "BadProperty")
        )

    def testStratisCliPartialChangeErrorFmt(self):
        """
        Test 'StratisCliPartialChangeError'
        """
        self._string_not_empty(
            StratisCliPartialChangeError(
                "Command",
                frozenset("ChangedResources"),
                frozenset("UnchangedResources"),
            )
        )

    def testStratisCliNoChangeErrorFmt(self):
        """
        Test 'StratisCliNoChangeError'
        """
        self._string_not_empty(
            StratisCliNoChangeError("Command", frozenset("ChangedResources"))
        )

    def testStratisCliIncoherenceErrorFmt(self):
        """
        Test 'StratisCliIncoherenceError'
        """
        self._string_not_empty(StratisCliIncoherenceError("Error"))

    def testStratisCliInUseErrorFmt(self):
        """
        Test 'StratisCliInUseError'
        """
        self._string_not_empty(
            StratisCliInUseError(frozenset("Blockdevs"), BlockDevTiers(0))
        )

    def testStratisCliUnknownInterfaceErrorFmt(self):
        """
        Test 'StratisCliUnknownInterfaceError'
        """
        self._string_not_empty(StratisCliUnknownInterfaceError("BadInterface"))

    def testTimeoutStratisCliEngineErrorFmt(self):
        """
        Test 'StratisCliEngineError'
        """
        self._string_not_empty(StratisCliEngineError(42, "Message"))

    def testStratisCliActionErrorFmt(self):
        """
        Test 'StratisCliActionError'
        """
        self._string_not_empty(
            StratisCliActionError(["CommandLineArgs"], argparse.ArgumentParser())
        )

    def testStratisCliGenerationErrorFmt(self):
        """
        Test 'StratisCliGenerationError'
        """
        self._string_not_empty(StratisCliGenerationError("Error"))

    def testStratisCliEnvironmentErrorFmt(self):
        """
        Test 'StratisCliEnvironmentError'
        """
        self._string_not_empty(StratisCliEnvironmentError("Error"))
