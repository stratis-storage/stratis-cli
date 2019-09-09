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
Utility functions for blackbox testing.
"""
import os
import random
import string
from subprocess import Popen, PIPE


def random_string(length=4):
    """
    Generates a random string
    :param length: Length of random string
    :return: String
    """
    return "{0}".format(
        "".join(random.choice(string.ascii_uppercase) for _ in range(length))
    )


def stratis_link(pool_name, fs_name=None):
    """
    Generate the stratis symlink for the pool and optionally for FS
    :param pool_name:
    :param fs_name:
    :return: Full path and name to symlink
    """
    fs_path = os.path.join(os.path.sep + "stratis", pool_name)
    if fs_name:
        fs_path = os.path.join(fs_path, fs_name)
    return fs_path


def process_exists(name):
    """
    Walk the process table looking for executable 'name', returns pid if one
    found, else return None
    """
    for pid in [pid for pid in os.listdir("/proc") if pid.isdigit()]:
        try:
            exe_name = os.readlink(os.path.join("/proc/", pid, "exe"))
        except OSError:
            continue
        if exe_name and exe_name.endswith(os.path.join("/", name)):
            return pid
    return None


def umount_mdv():
    """
    Locate and umount any stratis mdv mounts
    :return: None
    """
    with open("/proc/self/mounts", "r") as mounts:
        for line in mounts.readlines():
            if "/stratis/.mdv-" in line:
                mountpoint = line.split()[1]
                exec_command(["umount", mountpoint])


def exec_command(cmd):
    """
    Executes the specified infrastructure command.

    :param cmd: command to execute
    :type cmd: list of str
    :returns: standard output
    :rtype: str
    :raises AssertionError: if exit code is non-zero
    """
    process = Popen(cmd, stdout=PIPE, stderr=PIPE, close_fds=True, env=os.environ)
    result = process.communicate()
    stdout_text = bytes(result[0]).decode("utf-8")
    stderr_text = bytes(result[1]).decode("utf-8")

    expected_exit_code = 0

    if expected_exit_code != process.returncode:
        print(
            "cmd = %s [%d != %d]" % (str(cmd), expected_exit_code, process.returncode)
        )
        print("STDOUT= %s" % stdout_text)
        print("STDERR= %s" % stderr_text)

    assert expected_exit_code == process.returncode
    return stdout_text


def exec_test_command(cmd):
    """
    Executes the specified test command
    :param cmd: Command and arguments as list
    :type cmd: list of str
    :returns: (exit code, std out text, std err text)
    :rtype: triple of int * str * str
    """
    process = Popen(cmd, stdout=PIPE, stderr=PIPE, close_fds=True, env=os.environ)
    result = process.communicate()
    return (
        process.returncode,
        bytes(result[0]).decode("utf-8"),
        bytes(result[1]).decode("utf-8"),
    )
