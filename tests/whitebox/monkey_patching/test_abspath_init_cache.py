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
Test handing of relative paths
"""

# isort: STDLIB
import os

# isort: LOCAL
import stratis_cli
from stratis_cli._stratisd_constants import StratisdErrors

from .._misc import RUNNER, TEST_RUNNER, SimTestCase


class RelativePathInitCache(SimTestCase):
    """
    Test that relative path is converted to absolute
    """

    _POOLNAME = "mypool"

    def setUp(self):
        """
        Start stratisd and set up a pool
        """
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME, "./device1"]
        RUNNER(command_line)

    def test_init_cache_relative_path(self):
        """
        Verify that init-cache receives abolute path
        """

        def absolute_path_check(self, _, args):
            self.assertTrue(all(os.path.isabs(path) for path in args["devices"]))
            return ((True, args["devices"]), StratisdErrors.OK, "")

        # pylint: disable=import-outside-toplevel
        from stratis_cli._actions import _data

        # pylint: disable=protected-access
        stratis_cli._actions._data.Pool.Methods.InitCacheDevs = absolute_path_check
        command_line = [
            "--propagate",
            "pool",
            "init-cache",
            self._POOLNAME,
            "./fake/relative/path",
            "~/very/fake/path",
            "/fake/path",
        ]
        TEST_RUNNER(command_line)
