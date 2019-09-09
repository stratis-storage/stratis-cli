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
Wrapper around stratis CLI
"""
import os

from .utils import exec_command, rs, umount_mdv, stratis_link

# Some packaged systems might place this in /usr/sbin
STRATIS_CLI = os.getenv("STRATIS_CLI", "/usr/bin/stratis")

# Name prefix, so that we hopefully don't destroy any end user data by mistake!
TEST_PREF = os.getenv("STRATIS_UT_PREFIX", "STRATI$_DE$TROY_ME!_")


def p_n():
    """
    Return a random pool name
    :return: Random String
    """
    return TEST_PREF + "pool" + rs()


def fs_n():
    """
    Return a random FS name
    :return: Random String
    """
    return TEST_PREF + "fs" + rs()


class StratisCli:
    """
    Wrappers around stratis cli command-line calls.
    """

    @staticmethod
    def pool_list():
        """
        Query the pools
        :return: A list of pool names.
        """
        lines = exec_command([STRATIS_CLI, "pool", "list"])[0].splitlines()[1:]

        return [
            fields[0]
            for fields in [line.split() for line in lines]
            if fields[0].startswith(TEST_PREF)
        ]

    @staticmethod
    def fs_list():
        """
        Query the file systems
        :return: A dict,  Key being the fs name, the value being its pool name.
        """
        lines = exec_command([STRATIS_CLI, "fs", "list"])[0].splitlines()[1:]

        return dict(
            (fields[1], fields[0])
            for fields in [line.split() for line in lines]
            if fields[0].startswith(TEST_PREF)
        )

    @staticmethod
    def pool_destroy(name):
        """
        Destroy a pool
        :param name: Name of pool to destroy
        :return: None
        """
        if name.startswith(TEST_PREF):
            exec_command([STRATIS_CLI, "pool", "destroy", name])

    @staticmethod
    def destroy_all():
        """
        Destroys all Stratis FS and pools!
        :return: None
        """
        umount_mdv()

        # Remove FS
        for name, pool_name in StratisCli.fs_list().items():
            StratisCli.fs_destroy(pool_name, name)

        # Remove Pools
        for name in StratisCli.pool_list():
            StratisCli.pool_destroy(name)

    @staticmethod
    def fs_destroy(pool_name, fs_name):
        """
        Destroy a FS
        :param pool_name:  Pool which contains the FS
        :param fs_name: Name of FS to destroy
        :return: None
        """
        if pool_name.startswith(TEST_PREF):
            exec_command([STRATIS_CLI, "fs", "destroy", pool_name, fs_name])
            full_path = stratis_link(pool_name, fs_name)
            assert os.path.exists(full_path) is False


def clean_up():
    """
    Try to clean up after a test failure.

    :return: None
    """
    StratisCli.destroy_all()
    assert StratisCli.pool_list() == []
