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
Test error class formatting.
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
    Test various timeout inputs.
    """

    def testStratisCliErrorFmt(self):
        """
        Test 'StratisCliError'
        """
        exception = StratisCliError("Error")
        self.assertNotEqual(str(exception), "")

    def testStratisCliRuntimeErrorFmt(self):
        """
        Test 'StratisCliRuntimeError'
        """
        exception = StratisCliRuntimeError("Error")
        self.assertNotEqual(str(exception), "")

    def testStratisCliPropertyNotFoundErrorFmt(self):
        """
        Test 'StratisCliPropertyNotFoundError'
        """
        exception = StratisCliPropertyNotFoundError("BadInterface", "BadProperty")
        self.assertNotEqual(str(exception), "")

    def testStratisCliPartialChangeErrorFmt(self):
        """
        Test 'StratisCliPartialChangeError'
        """
        exception = StratisCliPartialChangeError(
            "Command", frozenset("ChangedResources"), frozenset("UnchangedResources")
        )
        self.assertNotEqual(str(exception), "")

    def testStratisCliNoChangeErrorFmt(self):
        """
        Test 'StratisCliNoChangeError'
        """
        exception = StratisCliNoChangeError("Command", frozenset("ChangedResources"))
        self.assertNotEqual(str(exception), "")

    def testStratisCliIncoherenceErrorFmt(self):
        """
        Should fail because the timeout value is a float.
        """
        exception = StratisCliIncoherenceError("Error")
        self.assertNotEqual(str(exception), "")

    def testStratisCliInUseErrorFmt(self):
        """
        Should fail because the timeout value is not an integer.
        """
        exception = StratisCliInUseError(frozenset("Blockdevs"), BlockDevTiers(0))
        self.assertNotEqual(str(exception), "")

    def testStratisCliUnknownInterfaceErrorFmt(self):
        """
        Test 'StratisCliUnknownInterfaceError'
        """
        exception = StratisCliUnknownInterfaceError("BadInterface")
        self.assertNotEqual(str(exception), "")

    def testTimeoutStratisCliEngineErrorFmt(self):
        """
        Test 'StratisCliEngineError'
        """
        exception = StratisCliEngineError(42, "Message")
        self.assertNotEqual(str(exception), "")

    def testStratisCliActionErrorFmt(self):
        """
        Test 'StratisCliActionError'
        """
        exception = StratisCliActionError(
            ["CommandLineArgs"], argparse.ArgumentParser()
        )
        self.assertNotEqual(str(exception), "")

    def testStratisCliGenerationErrorFmt(self):
        """
        Test 'StratisCliGenerationError'
        """
        exception = StratisCliGenerationError("Error")
        self.assertNotEqual(str(exception), "")

    def testStratisCliEnvironmentErrorFmt(self):
        """
        Test 'StratisCliEnvironmentError'
        """
        exception = StratisCliEnvironmentError("Error")
        self.assertNotEqual(str(exception), "")
