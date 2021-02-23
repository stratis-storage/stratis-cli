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
import signal
import string
import subprocess
import sys
import time
import unittest

# isort: THIRDPARTY
import psutil

# isort: LOCAL
from stratis_cli import run
from stratis_cli._error_reporting import handle_error
from stratis_cli._errors import StratisCliActionError


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
    Handle starting and stopping the stratisd daemon.
    """

    def setup(self):
        """
        Start the stratisd daemon with the simulator.
        """
        try:
            stratisd_var = os.environ["STRATISD"]
        except KeyError:
            raise RuntimeError(
                "STRATISD environment variable must be set to absolute path of stratisd executable"
            )
        self._stratisd = (  # pylint: disable=attribute-defined-outside-init
            subprocess.Popen(
                [os.path.join(stratisd_var), "--sim"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        )
        time.sleep(1)

    def teardown(self):
        """
        Stop the stratisd simulator and daemon.

        :return: a tuple of stdout and stderr.
        """
        self._stratisd.send_signal(signal.SIGINT)
        return self._stratisd.communicate()

    def cleanup(self):
        """
        Stop the daemon if it has been started.

        If the daemon has been started print the daemon log entries.
        """
        if hasattr(self, "_stratisd"):
            (_, stderrdata) = self.teardown()

            print("", file=sys.stdout, flush=True)
            print(
                "Log output from this invocation of stratisd:",
                file=sys.stdout,
                flush=True,
            )
            print(stderrdata, file=sys.stdout, flush=True)


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
        self.assertIsInstance(error_string, str)
        self.assertNotEqual(error_string, "")

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
                if psutil.Process(pid).name() == "stratisd":
                    raise RuntimeError(
                        "Evidently a stratisd process with process id %u is running"
                        % pid
                    )
            except psutil.NoSuchProcess:
                pass

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = _Service()
        self.addCleanup(self._service.cleanup)
        self._service.setup()


RUNNER = run()


class StratisCliTestRunError(AssertionError):
    """
    Exception that occurs after a TEST_RUNNER failure.
    """

    def __str__(self):
        return "Unexpected failure of command-line call in test"


def test_runner(command_line):
    """
    Execute the RUNNER method, and if it encounters a StratisCliActionError,
    raise a StratisCliTestRunError to display the exception contents.

    :param command_line: the command line arguments
    :type command_line: list
    """
    try:
        RUNNER(command_line)
    except StratisCliActionError as err:
        raise StratisCliTestRunError from err


TEST_RUNNER = test_runner
