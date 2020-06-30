# Copyright 2020 Red Hat, Inc.
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
Test handling of incompatible stratisd version
"""

# isort: LOCAL
import stratis_cli
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import StratisCliStratisdVersionError

from .._misc import SimTestCase

_ERROR = StratisCliErrorCodes.ERROR


class StratisdVersionTestCase(SimTestCase):
    """
    Test behavior of stratis on incompatible versions of stratisd.
    """

    def test_outdated_stratisd_version(self):
        """
        Verify that an outdated version of stratisd will produce a StratisCliStratisdVersionError.
        """

        def outdated_stratisd_version(_):
            """
            Return an outdated stratisd version.
            """
            return "1.0.0"

        # pylint: disable=import-outside-toplevel
        from stratis_cli._actions import _data

        # pylint: disable=protected-access
        stratis_cli._actions._data.Manager.Properties.Version.Get = (
            outdated_stratisd_version
        )

        command_line = ["--propagate", "daemon", "version"]
        self.check_error(StratisCliStratisdVersionError, command_line, _ERROR)
