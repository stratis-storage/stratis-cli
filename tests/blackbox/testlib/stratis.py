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
import datetime
import os
import time

from .utils import exec_command, rs, umount_mdv, stratis_link, size_representation

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
        :return: A dict,  Key being the pool name, the value being a dict with
                          keys [SIZE, USED]
        """
        # pylint: disable=too-many-locals
        cmd = [STRATIS_CLI, "pool", "list"]
        std_out, _ = exec_command(cmd)
        lines = std_out.splitlines()

        header = lines.pop(0).strip().replace(" ", "")
        assert header == "NameTotalPhysicalSizeTotalPhysicalUsed"

        rc = {}
        for l in lines:
            name, size, size_units, used, used_units = l.split()

            if name.startswith(TEST_PREF):
                rc[name] = dict(
                    SIZE=size_representation(size, size_units),
                    USED=size_representation(used, used_units),
                )
        return rc

    @staticmethod
    def fs_list():
        """
        Query the file systems
        :return: A dict,  Key being the fs name, the value being a dict with
                          keys [POOL_NAME, USED_SIZE, UUID, SYM_LINK, CREATED,
                                CREATED_TS]
        """
        # pylint: disable=too-many-locals
        cmd = [STRATIS_CLI, "fs", "list"]

        std_out, _ = exec_command(cmd)
        lines = std_out.splitlines()

        header = lines.pop(0).strip().replace(" ", "")
        assert header == "PoolNameNameUsedCreatedDeviceUUID"

        rc = {}
        for l in lines:
            pool_name, name, used, used_units, month, day, year, hr_min, sym_link, uuid = (
                l.split()
            )

            if not pool_name.startswith(TEST_PREF):
                continue

            created = "%s %s %s %s" % (month, day, year, hr_min)
            ts = time.mktime(
                datetime.datetime.strptime(created, "%b %d %Y %H:%M").timetuple()
            )

            rc[name] = dict(
                POOL_NAME=pool_name,
                USED_SIZE=size_representation(used, used_units),
                UUID=uuid,
                SYM_LINK=sym_link,
                CREATED=created,
                CREATED_TS=ts,
            )

        return rc

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
        for name, fs in StratisCli.fs_list().items():
            StratisCli.fs_destroy(fs["POOL_NAME"], name)

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
