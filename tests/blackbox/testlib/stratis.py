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

from .utils import exec_command, umount_mdv, TEST_PREF

# Some packaged systems might place this in /usr/sbin
STRATIS_CLI = os.getenv("STRATIS_CLI", "/usr/bin/stratis")


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
        lines = exec_command([STRATIS_CLI, "pool", "list"]).splitlines()[1:]

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
        lines = exec_command([STRATIS_CLI, "fs", "list"]).splitlines()[1:]

        return dict(
            (fields[1], fields[0])
            for fields in [line.split() for line in lines]
            if fields[0].startswith(TEST_PREF)
        )

    @staticmethod
    def destroy_all():
        """
        Destroys all Stratis FS and pools!
        :return: None
        """
        umount_mdv()

        # Remove FS
        for fs_name, pool_name in StratisCli.fs_list().items():
            exec_command([STRATIS_CLI, "fs", "destroy", pool_name, fs_name])

        # Remove Pools
        for name in StratisCli.pool_list():
            exec_command([STRATIS_CLI, "pool", "destroy", name])


def clean_up():
    """
    Try to clean up after a test failure.

    :return: None
    """
    StratisCli.destroy_all()
    assert StratisCli.pool_list() == []
