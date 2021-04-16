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

from .._misc import TEST_RUNNER, SimTestCase


class RelativePathCreatePool(SimTestCase):
    """
    Test that relative path is converted to absolute
    """

    def test_create_pool_relative_path(self):
        """
        Verify that create pool receives absolute path
        """

        def absolute_path_check(_, args):
            self.assertTrue(all(os.path.isabs(path) for path in args["devices"]))
            return ((True, (_, _)), StratisdErrors.OK, "")

        # pylint: disable=import-outside-toplevel
        from stratis_cli._actions import _data

        # pylint: disable=protected-access
        stratis_cli._actions._data.Manager.Methods.CreatePool = absolute_path_check

        command_line = [
            "--propagate",
            "pool",
            "create",
            "test_pool",
            "./fake/relative/path",
            "~/very/fake/path",
            "/fake/path",
        ]
        TEST_RUNNER(command_line)
