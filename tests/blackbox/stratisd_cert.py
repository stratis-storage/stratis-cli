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
Tests of stratisd.
"""

# isort: STDLIB
import argparse
import json
import os
import sys
import time
import unittest
from tempfile import NamedTemporaryFile

# isort: THIRDPARTY
import dbus
from testlib.dbus import StratisDbus, fs_n, p_n
from testlib.infra import KernelKey, clean_up
from testlib.utils import exec_command, process_exists

_ROOT = 0
_NON_ROOT = 1


def _raise_error_exception(return_code, msg, return_value_exists):
    """
    Check result of a D-Bus call in a context where it is in error
    if the call fails.
    :param int return_code: the return code from the D-Bus call
    :param str msg: the message returned on the D-Bus
    :param bool return_value_exists: whether a value representing
                                     a valid result was returned
    """
    if return_code != 0:
        raise RuntimeError(
            "Expected return code of 0; actual return code: %s, error_msg: %s"
            % (return_code, msg)
        )

    if not return_value_exists:
        raise RuntimeError(
            "Result value was default or placeholder value and does not represent a valid result"
        )


def make_test_pool(pool_name, pool_disks):
    """
    Create a test pool that will later get destroyed
    :param str pool_name: Name of the pool to be created
    :param list pool_disks: List of disks with which the pool will be created
    :return: Object path of the created pool
    """
    (obj_path_exists, (obj_path, _)), return_code, msg = StratisDbus.pool_create(
        pool_name, pool_disks, None
    )

    _raise_error_exception(return_code, msg, obj_path_exists)
    return obj_path


def make_test_filesystem(pool_path, fs_name):
    """
    Create a test filesystem that will later get destroyed
    :param str pool_path: Object path of a test pool
    :param str fs_name: Name of the filesystem to be created
    :return: Object path of the created filesystem
    """
    (
        filesystems_created,
        (array_of_tuples_with_obj_paths_and_names),
    ), return_code, msg = StratisDbus.fs_create(pool_path, fs_name)

    _raise_error_exception(return_code, msg, filesystems_created)
    return array_of_tuples_with_obj_paths_and_names[0][0]


class StratisCertify(unittest.TestCase):  # pylint: disable=too-many-public-methods
    """
    Unit tests for Stratis
    """

    def setUp(self):
        """
        Setup for an individual test.
        * Register a cleanup action, to be run if the test fails.
        * Ensure that stratisd is running via systemd.
        * Use the running stratisd instance to destroy any existing
        Stratis filesystems, pools, etc.
        * Call "udevadm settle" so udev database can be updated with changes
        to Stratis devices.
        :return: None
        """
        self.addCleanup(clean_up)

        if process_exists("stratisd") is None:
            exec_command(["systemctl", "start", "stratisd"])
            time.sleep(20)

        clean_up()

        time.sleep(1)
        exec_command(["udevadm", "settle"])

    def _inequality_test(self, result, expected_non_result):
        """
        :param object result: the result of a test
        :param object expected_non_result: a value which the result must
                                           not match, but which has the
                                           expected type
        """
        self.assertIsInstance(result, type(expected_non_result))
        self.assertNotEqual(result, expected_non_result)

    def _unittest_command(self, result, expected_return_code):
        """
        :param result: a tuple of the (optional) return value, the
                       return code, and the return message from a
                       D-Bus call
        :type result: tuple of object * dbus.UInt16 * str OR tuple
                      of dbus.UInt16 * str if there is no return value
        :raises: AssertionError if the actual return code is not
                 equal to the expected return code
        """
        if len(result) == 3:
            (_, return_code, msg) = result
        else:
            (return_code, msg) = result

        self.assertEqual(return_code, expected_return_code, msg=msg)

    def _test_permissions(self, dbus_method, args, permissions):
        """
        Test running dbus_method with and without root permissions.
        :param dbus_method: D-Bus method to be tested
        :type dbus_method: StratisDbus method
        :param args: the arguments to be passed to the D-Bus method
        :type args: list of objects
        :param bool permissions: True if dbus_method needs root permissions to succeed.
                                False if dbus_method should succeed without root permissions.
        """
        _permissions_flag = False

        euid = os.geteuid()
        if euid != _ROOT:
            raise RuntimeError(
                "This process should be running as root, but the current euid is %d."
                % euid
            )
        dbus_method(*args)

        os.seteuid(_NON_ROOT)
        StratisDbus.reconnect()

        try:
            dbus_method(*args)
        except dbus.exceptions.DBusException as err:
            if err.get_dbus_name() == "org.freedesktop.DBus.Error.AccessDenied":
                _permissions_flag = True
            else:
                os.seteuid(_ROOT)
                raise err
        except Exception as err:
            os.seteuid(_ROOT)
            raise err

        os.seteuid(_ROOT)
        StratisDbus.reconnect()
        self.assertEqual(_permissions_flag, permissions)

    def test_get_managed_objects(self):
        """
        Test that GetManagedObjects returns a dict w/out failure.
        """
        self._inequality_test(StratisDbus.get_managed_objects(), {})

    def test_get_managed_objects_permissions(self):
        """
        Test that GetManagedObjects succeeds when root permissions are dropped.
        """
        self._test_permissions(StratisDbus.get_managed_objects, [], False)

    def test_stratisd_version(self):
        """
        Test getting the daemon version.
        """
        self._inequality_test(StratisDbus.stratisd_version(), "")

    def test_stratisd_version_permissions(self):
        """
        Test that getting daemon version succeeds when permissions are dropped.
        """
        self._test_permissions(StratisDbus.stratisd_version, [], False)

    def test_pool_list_empty(self):
        """
        Test listing an non-existent pool.
        """
        result = StratisDbus.pool_list()
        self.assertEqual(result, [])

    def test_pool_list_permissions(self):
        """
        Test listing pool succeeds when root permissions are dropped.
        """
        self._test_permissions(StratisDbus.pool_list, [], False)

    def test_blockdev_list(self):
        """
        Test listing a blockdev.
        """
        result = StratisDbus.blockdev_list()
        self.assertEqual(result, [])

    def test_blockdev_list_permissions(self):
        """
        Test that listing blockdevs suceeds when root permissions are dropped.
        """
        self._test_permissions(StratisDbus.blockdev_list, [], False)

    def test_filesystem_list_empty(self):
        """
        Test listing an non-existent filesystem.
        """
        result = StratisDbus.fs_list()
        self.assertEqual(result, {})

    def test_filesystem_list_permissions(self):
        """
        Test that listing filesystem suceeds when root permissions are dropped.
        """
        self._test_permissions(StratisDbus.fs_list, [], False)

    def test_key_set_unset(self):
        """
        Test setting a key.
        """
        key_desc = "test-description"

        with NamedTemporaryFile(mode="w") as temp_file:
            temp_file.write("test-password")
            temp_file.flush()

            self._unittest_command(
                StratisDbus.set_key(key_desc, temp_file), dbus.UInt16(0)
            )

        self._unittest_command(StratisDbus.unset_key(key_desc), dbus.UInt16(0))

    def test_key_set_unset_permissions(self):
        """
        Test setting and unsetting a key fails when root permissions are dropped.
        """
        key_desc = "test-description"

        with NamedTemporaryFile(mode="w") as temp_file:
            temp_file.write("test-password")
            temp_file.flush()

            self._test_permissions(StratisDbus.set_key, [key_desc, temp_file], True)

        self._test_permissions(StratisDbus.unset_key, [key_desc], True)

    def test_pool_create(self):
        """
        Test creating a pool.
        """
        pool_name = p_n()

        self._unittest_command(
            StratisDbus.pool_create(pool_name, StratisCertify.DISKS, None),
            dbus.UInt16(0),
        )

    def test_pool_create_permissions(self):
        """
        Test that creating a pool fails when root permissions are dropped.
        """
        pool_name = p_n()
        self._test_permissions(
            StratisDbus.pool_create, [pool_name, StratisCertify.DISKS, None], True
        )

    def test_pool_create_encrypted(self):
        """
        Test creating an encrypted pool.
        """
        with KernelKey("test-password") as key_desc:
            pool_name = p_n()

            self._unittest_command(
                StratisDbus.pool_create(pool_name, StratisCertify.DISKS, key_desc),
                dbus.UInt16(0),
            )

    def test_pool_add_cache(self):
        """
        Test adding cache to a pool.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        self._unittest_command(
            StratisDbus.pool_init_cache(pool_path, StratisCertify.DISKS[1:2]),
            dbus.UInt16(0),
        )
        self._unittest_command(
            StratisDbus.pool_add_cache(pool_path, StratisCertify.DISKS[2:3]),
            dbus.UInt16(0),
        )

    def test_pool_add_cache_permissions(self):
        """
        Test that adding cache to pool fails when root permissions are dropped.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        self._test_permissions(
            StratisDbus.pool_init_cache, [pool_path, StratisCertify.DISKS[1:2]], True
        )
        self._test_permissions(
            StratisDbus.pool_add_cache, [pool_path, StratisCertify.DISKS[2:3]], True
        )

    def test_pool_add_data(self):
        """
        Test adding data to a pool.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:2])

        self._unittest_command(
            StratisDbus.pool_add_data(pool_path, StratisCertify.DISKS[2:3]),
            dbus.UInt16(0),
        )

    def test_pool_add_data_permissions(self):
        """
        Test that adding data to a pool fails when root permissions are dropped.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:2])

        self._test_permissions(
            StratisDbus.pool_add_data, [pool_path, StratisCertify.DISKS[2:3]], True
        )

    def test_pool_list_not_empty(self):
        """
        Test listing an non-existent pool.
        """
        pool_name = p_n()
        make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        self._inequality_test(StratisDbus.pool_list(), [])

    def test_pool_create_same_name_and_devices(self):
        """
        Test creating a pool that already exists with the same devices.
        """
        pool_name = p_n()
        make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        self._unittest_command(
            StratisDbus.pool_create(pool_name, StratisCertify.DISKS[0:1], None),
            dbus.UInt16(0),
        )

    def test_pool_create_same_name_different_devices(self):
        """
        Test creating a pool that already exists with different devices.
        """
        pool_name = p_n()
        make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        self._unittest_command(
            StratisDbus.pool_create(pool_name, StratisCertify.DISKS[1:3], None),
            dbus.UInt16(1),
        )

    def test_pool_destroy(self):
        """
        Test destroying a pool.
        """
        pool_name = p_n()
        make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        self._unittest_command(StratisDbus.pool_destroy(pool_name), dbus.UInt16(0))

        self.assertEqual(StratisDbus.fs_list(), {})

    def test_pool_destroy_permissions(self):
        """
        Test that destroying a pool fails when root permissions are dropped.
        """
        pool_name = p_n()
        make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        self._test_permissions(StratisDbus.pool_destroy, [pool_name], True)

    def test_filesystem_create(self):
        """
        Test creating a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()

        self._unittest_command(
            StratisDbus.fs_create(pool_path, fs_name), dbus.UInt16(0)
        )

    def test_filesystem_create_permissions(self):
        """
        Test that creating a filesystem fails when root permissions are dropped.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()

        self._test_permissions(StratisDbus.fs_create, [pool_path, fs_name], True)

    def test_filesystem_rename(self):
        """
        Test renaming a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        fs_name_rename = fs_n()

        self._unittest_command(
            StratisDbus.fs_rename(fs_name, fs_name_rename), dbus.UInt16(0)
        )

    def test_filesystem_rename_permissions(self):
        """
        Test that renaming a filesystem fails when root permissions are dropped.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        fs_name_rename = fs_n()

        self._test_permissions(StratisDbus.fs_rename, [fs_name, fs_name_rename], True)

    def test_filesystem_rename_same_name(self):
        """
        Test renaming a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        self._unittest_command(StratisDbus.fs_rename(fs_name, fs_name), dbus.UInt16(0))

    def test_filesystem_snapshot(self):
        """
        Test snapshotting a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()
        fs_path = make_test_filesystem(pool_path, fs_name)

        snapshot_name = fs_n()

        self._unittest_command(
            StratisDbus.fs_snapshot(pool_path, fs_path, snapshot_name), dbus.UInt16(0)
        )

    def test_filesystem_snapshot_permissions(self):
        """
        Test snapshotting a filesystem fails when root permissions are dropped.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()
        fs_path = make_test_filesystem(pool_path, fs_name)

        snapshot_name = fs_n()

        self._test_permissions(
            StratisDbus.fs_snapshot, [pool_path, fs_path, snapshot_name], True
        )

    def test_filesystem_list_not_empty(self):
        """
        Test listing an existent filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        self._inequality_test(StratisDbus.fs_list(), {})

    def test_filesystem_create_same_name(self):
        """
        Test creating a filesystem that already exists.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        self._unittest_command(
            StratisDbus.fs_create(pool_path, fs_name), dbus.UInt16(0)
        )

    def test_filesystem_destroy(self):
        """
        Test destroying a filesystem.
        """
        pool_name = p_n()
        pool_path = make_test_pool(pool_name, StratisCertify.DISKS[0:1])

        fs_name = fs_n()
        make_test_filesystem(pool_path, fs_name)

        self._unittest_command(
            StratisDbus.fs_destroy(pool_name, fs_name), dbus.UInt16(0)
        )

        self.assertEqual(StratisDbus.fs_list(), {})

    def test_get_report(self):
        """
        Test getting a valid and invalid report.
        """
        (result, return_code, _) = StratisDbus.get_report("errored_pool_report")
        self._inequality_test(result, dbus.String(""))
        self.assertEqual(return_code, dbus.UInt16(0))
        # Test that we have received valid JSON.
        json.loads(result)

        (result, return_code, _) = StratisDbus.get_report("invalid_report")
        self.assertEqual(result, dbus.String(""))
        self._inequality_test(return_code, dbus.UInt16(0))

    def test_get_report_permissions(self):
        """
        Test that getting a valid report fails when root permissions are dropped.
        """
        self._test_permissions(StratisDbus.get_report, ["errored_pool_report"], True)


def main():
    """
    The main method.
    """
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "--disk",
        action="append",
        dest="DISKS",
        default=[],
        help="disks to use, a minimum of 3 in order to run every test",
    )
    parsed_args, unittest_args = argument_parser.parse_known_args()
    StratisCertify.DISKS = parsed_args.DISKS
    print("Using block device(s) for tests: %s" % StratisCertify.DISKS)
    unittest.main(argv=sys.argv[:1] + unittest_args)


if __name__ == "__main__":
    main()
