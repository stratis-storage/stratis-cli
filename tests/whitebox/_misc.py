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
Miscellaneous methods to support testing.
"""

# isort: STDLIB
import os
import random
import string
import subprocess
import sys
import time
import unittest

# isort: THIRDPARTY
import psutil

# isort: LOCAL
from stratis_cli import handle_error, run
from stratis_cli._errors import StratisCliActionError

try:
    _STRATISD = os.environ["STRATISD"]
except KeyError:
    message = "STRATISD environment variable must be set to absolute path of stratisd executable"
    sys.exit(message)


def device_name_list(min_devices=0, max_devices=10):
    """
    Return a function that returns a random list of device names based on
    parameters.
    """

    def the_func():
        return [
            "/dev/%s"
            % "".join(
                random.choice(string.ascii_uppercase + string.digits) for _ in range(4)
            )
            for _ in range(random.randrange(min_devices, max_devices + 1))
        ]

    return the_func


class _Service:
    """
    Handle starting and stopping the Rust service.
    """

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._stratisd = subprocess.Popen([os.path.join(_STRATISD), "--sim"])
        time.sleep(1)

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._stratisd.terminate()
        self._stratisd.wait()

    def cleanup(self):
        """
        Stop the daemon if it has been started.
        """
        if hasattr(self, "_stratisd"):
            self.tearDown()


class RunTestCase(unittest.TestCase):
    """
    Test case for running the program.
    """

    def check_error(self, expected_cause, command_line, expected_code):
        """
        Check that the expected exception was raised, and that the cause
        and exit codes were also as expected, based on the command line
        arguments passed to the program.

        Precondition: command_line contains the "--propagate" flag, so that
        the exception is propagated by the source, and can thus be caught
        in the test.

        :param expected_cause: the expected exception below the StratisCliActionError
        :type expected_cause: Exception
        :param command_line: the command line arguments
        :type command_line: list
        :param expected_code: the expected error code
        :type expected_code: int
        """
        with self.assertRaises(StratisCliActionError) as context:
            RUNNER(command_line)

        exception = context.exception
        cause = exception.__cause__
        self.assertIsInstance(cause, expected_cause)

        error_string = str(exception)
        self.assertNotEqual(error_string, None)
        self.assertIsInstance(error_string, str)

        with self.assertRaises(SystemExit) as final_err:
            handle_error(exception)

        final_code = final_err.exception.code
        self.assertEqual(final_code, expected_code)

    def check_system_exit(self, command_line, expected_code):
        """
        Check that SystemExit exception was raised with the expected error
        code as a result of running the program.

        :param command_line: the command line arguments
        :type command_line: list
        :param expected_code: the expected error code
        :type expected_code: int
        """
        with self.assertRaises(SystemExit) as context:
            RUNNER(command_line)
        exit_code = context.exception.code
        self.assertEqual(exit_code, expected_code)


class SimTestCase(RunTestCase):
    """
    A SimTestCase must always start and stop stratisd (simulator vesion).
    """

    @classmethod
    def setUpClass(cls):
        """
        Assert that there are no other stratisd processes running.
        """
        for pid in psutil.pids():
            try:
                assert psutil.Process(pid).name() != "stratisd", (
                    "Evidently a stratisd process with process id %u is running" % pid
                )
            except psutil.NoSuchProcess:
                pass

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = _Service()
        self.addCleanup(self._service.cleanup)
        self._service.setUp()


RUNNER = run()
