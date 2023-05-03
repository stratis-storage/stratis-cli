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
import subprocess  # nosec B404
import sys
import time
import unittest
from uuid import UUID

# isort: THIRDPARTY
import psutil

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes, run
from stratis_cli._actions._connection import get_object
from stratis_cli._actions._constants import TOP_OBJECT
from stratis_cli._error_reporting import handle_error
from stratis_cli._errors import StratisCliActionError

_OK = StratisCliErrorCodes.OK


def device_name_list(min_devices=0, max_devices=10, unique=False):
    """
    Return a function that returns a random list of device names based on
    parameters.

    :param int min_devices: the minimum number of device names to generate
    :param int max_devices: the maximum number of device names to generate
    :param bool unique: ensure that all device names are unique
    """

    def the_func():
        def random_string():
            return "".join(
                random.choice(string.ascii_uppercase + string.digits)  # nosec B311
                for _ in range(4)
            )

        return [
            f"/dev/{random_string()}"
            for _ in range(random.randrange(min_devices, max_devices + 1))  # nosec B311
        ]

    if unique:

        def the_unique_func():
            devices = set()
            while len(devices) < min_devices:
                for device in the_func():
                    devices.add(device)

            return list(devices)

        return the_unique_func

    return the_func


def split_device_list(devices, num_lists):
    """
    Split devices into num_lists distinct lists.

    :param devices: list of device names
    :type devices: list of str
    :param int num_lists: num of lists to return

    :rtype: list of list of str
    """
    num_devices = len(devices)
    indices = random.sample(range(1, num_devices), num_lists - 1)
    next_indices = indices[:]

    indices.append(0)
    indices.sort()

    next_indices.append(num_devices)
    next_indices.sort()

    return [devices[indices[n] : next_indices[n]] for n in range(len(indices))]


class _Service:
    """
    Handle starting and stopping the stratisd daemon.
    """

    # pylint: disable=consider-using-with
    def setup(self):
        """
        Start the stratisd daemon with the simulator.
        """
        try:
            stratisd_var = os.environ["STRATISD"]
        except KeyError as err:
            raise RuntimeError(
                "STRATISD environment variable must be set to absolute path of stratisd executable"
            ) from err
        self._stratisd = (  # pylint: disable=attribute-defined-outside-init
            subprocess.Popen(  # nosec 119
                [os.path.join(stratisd_var), "--sim"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
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
                        f"Evidently a stratisd process with process id {pid} is running"
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


_RUNNER = run()


def run_with_delay(command_line_args):
    """
    Wait 1/4 of a second before running stratis with the specified
    command-line arguments.

    :param command_line_args: the command line args to pass
    :type command_line_args: list of str
    """
    time.sleep(0.25)
    return _RUNNER(command_line_args)


RUNNER = run_with_delay


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


def get_pool(proxy, pool_name):
    """
    Get pool information given a pool name.

    :param proxy: D-Bus proxy object for top object
    :param str pool_name: the name of the pool with the D-Bus info
    :returns: pool object path and pool info
    :rtype: str * dict
    :raise DbusClientUniqueError:
    """
    # pylint: disable=import-outside-toplevel
    # isort: LOCAL
    from stratis_cli._actions._data import ObjectManager, pools

    managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
    return next(
        pools(props={"Name": pool_name})
        .require_unique_match(True)
        .search(managed_objects)
    )


def get_pool_blockdevs(proxy, pool_name):
    """
    Get a generator of blockdevs for a given pool.
    """
    pool_object_path, _ = get_pool(proxy, pool_name)

    # pylint: disable=import-outside-toplevel
    # isort: LOCAL
    from stratis_cli._actions._data import MODev, ObjectManager, devs

    managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
    return (
        (op, MODev(info))
        for (op, info) in devs(props={"Pool": pool_object_path}).search(managed_objects)
    )


def stop_pool(pool_name):
    """
    Stop a pool and return the UUID of the pool.
    This method exists because it is the most direct way to get the UUID of
    a pool that has just been stopped, for testing.

    :param str pool_name: the name of the pool to stop

    :returns: the UUID of the stopped pool
    :rtype: UUID
    :raises: RuntimeError
    """

    # pylint: disable=import-outside-toplevel
    # isort: LOCAL
    from stratis_cli._actions._data import Manager

    proxy = get_object(TOP_OBJECT)

    ((stopped, pool_uuid), return_code, message) = Manager.Methods.StopPool(
        proxy, {"id_type": "name", "id": pool_name}
    )

    if not return_code == _OK:
        raise RuntimeError(f"Pool with name {pool_name} was not stopped: {message}")

    if not stopped:
        raise RuntimeError(
            f"Pool with name {pool_name} was supposed to have been started but was not"
        )

    return UUID(pool_uuid)
