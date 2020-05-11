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
Check version of stratisd
"""
# isort: THIRDPARTY
from semantic_version import Spec, Version

from .._errors import StratisCliStratisdVersionError
from ._connection import get_object
from ._constants import TOP_OBJECT


def check_stratisd_version():
    """
    Checks that the version of stratisd that is running is compatible with
    this version of the CLI.

    :raises StratisCliStratisdVersionError
    """
    from ._constants import MAXIMUM_STRATISD_VERSION, MINIMUM_STRATISD_VERSION
    from ._data import Manager

    version_spec = Spec(
        ">=%s,<%s" % (MINIMUM_STRATISD_VERSION, MAXIMUM_STRATISD_VERSION)
    )
    version = Manager.Properties.Version.Get(get_object(TOP_OBJECT))

    if Version(version) not in version_spec:
        raise StratisCliStratisdVersionError(
            version, MINIMUM_STRATISD_VERSION, MAXIMUM_STRATISD_VERSION
        )
