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

from .utils import exec_command, rs, umount_mdv, stratis_link, units_to_bytes

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
    @staticmethod
    def cli_version():
        """
        Returns version of command line
        :return: String representation of version
        """
        stdout, _ = exec_command([STRATIS_CLI, "--version"])
        return stdout.strip()

    @staticmethod
    def daemon_version():
        """
        Returns the version of daemon
        :return: String representation of version
        """
        stdout, _ = exec_command([STRATIS_CLI, "daemon", "version"])
        return stdout.strip()

    @staticmethod
    def daemon_redundancy():
        """
        Returns what redundancy the daemon supports
        :return: (Desc, int)
        """
        stdout, _ = exec_command([STRATIS_CLI, "daemon", "redundancy"])
        parsed = stdout.strip().replace(" ", "").split(":")
        return parsed[0], int(parsed[1])

    @staticmethod
    def pool_list(specify_list=True):
        """
        Query the pools
        :param specify_list: Use pool list syntax
        :return: A dict,  Key being the pool name, the value being a dict with
                          keys [SIZE, USED]
        """
        cmd = [STRATIS_CLI, "pool"]
        if specify_list:
            cmd.append("list")
        std_out, _ = exec_command(cmd)
        lines = std_out.splitlines()

        header = lines.pop(0).strip().replace(" ", "")
        assert header == "NameTotalPhysicalSizeTotalPhysicalUsed"

        rc = {}
        for l in lines:
            name, size, size_units, used, used_units = l.split()

            if name.startswith(TEST_PREF):
                rc[name] = dict(
                    SIZE=units_to_bytes(size, size_units),
                    USED=units_to_bytes(used, used_units))
        return rc

    @staticmethod
    def fs_list(specify_list=True):
        """
        Query the file systems
        :param specify_list: Use fs list syntax
        :return: A dict,  Key being the fs name, the value being a dict with
                          keys [POOL_NAME, USED_SIZE, UUID, SYM_LINK, CREATED,
                                CREATED_TS]
        """
        cmd = [STRATIS_CLI, "fs"]
        if specify_list:
            cmd.append("list")

        std_out, _ = exec_command(cmd)
        lines = std_out.splitlines()

        header = lines.pop(0).strip().replace(" ", "")
        assert header == "PoolNameNameUsedCreatedDeviceUUID"

        rc = {}
        for l in lines:
            pool_name, name, used, used_units, month, day, year, hr_min, \
                sym_link, uuid = l.split()

            if not pool_name.startswith(TEST_PREF):
                continue

            created = "%s %s %s %s" % (month, day, year, hr_min)
            ts = time.mktime(
                datetime.datetime.strptime(created,
                                           "%b %d %Y %H:%M").timetuple())
            now = time.time()

            # Everything we have created should have occurred very recently, but
            # our CI systems can be slow, so give them some time, we might need
            # to remove this assert if it becomes problematic.
            assert (now - ts) < 300.0

            rc[name] = dict(
                POOL_NAME=pool_name,
                USED_SIZE=units_to_bytes(used, used_units),
                UUID=uuid,
                SYM_LINK=sym_link,
                CREATED=created,
                CREATED_TS=ts)

        return rc

    @staticmethod
    def blockdev_list(specify_list=True):
        """
        Query the block devs
        :param specify_list: Use blockdev list syntax
        :return: A dict, Key is the device node, the value being a dict with
                         keys [POOL_NAME, SIZE, STATE, TIER]
        """
        cmd = [STRATIS_CLI, "blockdev"]
        if specify_list:
            cmd.append("list")

        std_out, _ = exec_command(cmd)
        lines = std_out.splitlines()

        header = lines.pop(0).strip().replace(" ", "")
        assert header == "PoolNameDeviceNodePhysicalSizeStateTier"

        rc = {}
        for l in lines:
            pool_name, device_node, size, size_units, state, tier = l.split()

            if pool_name.startswith(TEST_PREF):
                rc[device_node] = dict(
                    POOL_NAME=pool_name,
                    SIZE=units_to_bytes(size, size_units),
                    STATE=state,
                    TIER=tier)

        return rc

    @staticmethod
    def pool_create(name, block_devices):
        """
        Creates a pool
        :param name: Name of pool
        :param block_devices: List of block devices to use
        :return: None
        """
        exec_command([STRATIS_CLI, "pool", "create", name] + block_devices)

        # Work around for
        # https://bugzilla.redhat.com/show_bug.cgi?id=1687002
        umount_mdv()

        full_path = stratis_link(name)
        assert os.path.exists(full_path)
        assert os.path.isdir(full_path)

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
    def pool_rename(old_name, new_name):
        """
        Renames a pool
        :param old_name:    Current pool name
        :param new_name:    New pool name
        :return: None
        """
        if old_name.startswith(TEST_PREF) and new_name.startswith(TEST_PREF):
            exec_command([STRATIS_CLI, "pool", "rename", old_name, new_name])

            old_path = stratis_link(old_name)
            new_path = stratis_link(new_name)
            assert not os.path.exists(old_path)
            assert os.path.exists(new_path)
            assert os.path.isdir(new_path)

    @staticmethod
    def pool_add(pool_name, option, devices):
        """
        Adds one or more devices to a pool
        :param pool_name: Name of pool
        :param option: String, either ["add-cache", "add-data"]
        :param devices: List of devices to add
        :return: None
        """
        if pool_name.startswith(TEST_PREF):
            exec_command([STRATIS_CLI, "pool", option, pool_name] + devices)
            blockdevs = StratisCli.blockdev_list()
            for b in devices:
                assert b in blockdevs
                assert blockdevs[b]["POOL_NAME"] == pool_name

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
        for name in StratisCli.pool_list().keys():
            StratisCli.pool_destroy(name)

    @staticmethod
    def fs_create(pool_name, fs_name):
        """
        Create a FS
        :param pool_name: Pool to allocate FS from
        :param fs_name: FS name
        :return: None
        """
        if pool_name.startswith(TEST_PREF) and fs_name.startswith(TEST_PREF):
            exec_command([STRATIS_CLI, "fs", "create", pool_name, fs_name])

            # Check symlink
            full_path = stratis_link(pool_name, fs_name)
            assert os.path.exists(full_path)

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

    @staticmethod
    def fs_rename(pool_name, old_name, new_name):
        """
        Rename a FS
        :param pool_name: Pool which contains the FS
        :param old_name: Existing FS name
        :param new_name: New FS name
        :return: None
        """
        if pool_name.startswith(TEST_PREF):
            exec_command(
                [STRATIS_CLI, "fs", "rename", pool_name, old_name, new_name])

            assert not os.path.exists(stratis_link(pool_name, old_name))
            assert os.path.exists(stratis_link(pool_name, new_name))

    @staticmethod
    def fs_ss_create(pool_name, fs_name, snapshot_name):
        """
        Create a Snap shot
        :param pool_name: Pool which contains FS to snapshot
        :param fs_name: File system to snap shot
        :param snapshot_name: Name of snap shot
        :return: None
        """
        if pool_name.startswith(TEST_PREF):
            exec_command([
                STRATIS_CLI, "fs", "snapshot", pool_name, fs_name,
                snapshot_name
            ])

            # Check symlink
            full_path = stratis_link(pool_name, snapshot_name)
            assert os.path.exists(full_path)
