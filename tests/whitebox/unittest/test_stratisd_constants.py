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
Test 'stratisd_constants'.
"""

# isort: STDLIB
import unittest

# isort: LOCAL
from stratis_cli._error_codes import PoolMaintenanceErrorCode
from stratis_cli._stratisd_constants import PoolActionAvailability, StratisdErrors


class PoolActionAvailabilityTestCase(unittest.TestCase):
    """
    Test properties of PoolActionAvailability implementation
    """

    def test_conversion(self):
        """
        Test conversion from D-Bus value to pool maintenance error codes.
        """
        self.assertEqual(
            PoolActionAvailability.FULLY_OPERATIONAL.pool_maintenance_error_codes(), []
        )

        result = PoolActionAvailability.NO_IPC_REQUESTS.pool_maintenance_error_codes()
        self.assertEqual(result, [PoolMaintenanceErrorCode.NO_IPC_REQUESTS])

        result = PoolActionAvailability.NO_POOL_CHANGES.pool_maintenance_error_codes()
        self.assertEqual(len(result), 2)
        self.assertIn(PoolMaintenanceErrorCode.NO_IPC_REQUESTS, result)
        self.assertIn(PoolMaintenanceErrorCode.NO_POOL_CHANGES, result)


class StratisdErrorsTestCase(unittest.TestCase):
    """
    Test StratisdErrors
    """

    def test_str(self):
        """
        An OK EngineError is never constructed during stratis-cli operation.
        """
        self.assertEqual(str(StratisdErrors.OK), "OK")
