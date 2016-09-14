# Copyright 2016 Red Hat, Inc.
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
Miscellaneous actions about stratis.
"""

from __future__ import print_function

from .._constants import TOP_OBJECT

from .._dbus import Manager
from .._dbus import get_object

from .._errors import StratisCliImpossibleError

from ._stratisd_constants import StratisdRaidGen


class StratisActions(object):
    """
    Stratis actions.
    """
    # pylint: disable=too-few-public-methods

    @staticmethod
    def list_stratisd_log_level(namespace):
        """
        List the stratisd log level.
        """
        # pylint: disable=unused-argument
        proxy = get_object(TOP_OBJECT)
        print(Manager(proxy).LogLevel)
        return

    @staticmethod
    def list_stratisd_redundancy(namespace):
        """
        List the stratisd redundancy designations.
        """
        # pylint: disable=unused-argument
        levels = StratisdRaidGen.get_object()
        for x in levels.FIELDS:
            print("%s: %d" % (x, getattr(levels, x)))
        return

    @staticmethod
    def list_stratisd_version(namespace):
        """
        List the stratisd version.
        """
        # pylint: disable=unused-argument
        proxy = get_object(TOP_OBJECT)
        print(Manager(proxy).Version)
        return

    @staticmethod
    def dispatch(namespace):
        """
        Dispatch to the correct function.
        """
        if namespace.log_level:
            StratisActions.list_stratisd_log_level(namespace)
            return

        if namespace.redundancy:
            StratisActions.list_stratisd_redundancy(namespace)
            return

        if namespace.version:
            StratisActions.list_stratisd_version(namespace)
            return

        raise StratisCliImpossibleError(
           "Exactly one option should have been selected."
        )
        # pylint: disable=unreachable
        return
