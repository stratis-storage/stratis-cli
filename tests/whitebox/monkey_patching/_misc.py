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
Miscellaneous methods to support testing.
"""

# isort: STDLIB
import os

# isort: LOCAL
from stratis_cli._stratisd_constants import StratisdErrors

from .._misc import SimTestCase


class PathTestCase(SimTestCase):
    """
    A PathTestCase includes method to check if paths are formatted as absolute.
    """

    def absolute_path_check(self, _, args):
        """
        Verify that all paths passed to method are absolute
        """
        self.assertTrue(all(os.path.isabs(path) for path in args["devices"]))
        return ((True, args["devices"]), StratisdErrors.OK, "")
