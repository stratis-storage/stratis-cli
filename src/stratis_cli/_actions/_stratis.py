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

from stratisd_client_dbus import Manager
from stratisd_client_dbus import StratisdRaidGen
from stratisd_client_dbus import get_object

from .._constants import TOP_OBJECT


class StratisActions(object):
    """
    Stratis actions.
    """

    @staticmethod
    def list_stratisd_redundancy(namespace):
        """
        List the stratisd redundancy designations.
        """
        # pylint: disable=unused-argument
        levels = StratisdRaidGen.get_object()
        for x in levels.fields():
            print("%s: %d" % (x, getattr(levels, x)))
        return

    @staticmethod
    def list_stratisd_version(namespace):
        """
        List the stratisd version.
        """
        # pylint: disable=unused-argument
        print("%s" % Manager.Properties.Version(get_object(TOP_OBJECT)))
