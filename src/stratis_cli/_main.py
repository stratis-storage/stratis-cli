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
Highest level runner.
"""
import sys

import dbus

from dbus_python_client_gen import DPClientRuntimeError

from ._errors import StratisCliError
from ._parser import gen_parser


def run():
    """
    Generate a function that parses arguments and executes.
    """
    parser = gen_parser()

    def the_func(command_line_args):
        """
        Run according to the arguments passed.
        """
        result = parser.parse_args(command_line_args)
        try:
            result.func(result)
        # Catch exceptions separately to make use of more sophisticated
        # DBusException get_dbus_message() method.
        except dbus.exceptions.DBusException as err:
            if result.propagate:
                raise
            sys.exit("Execution failed: %s" % err.get_dbus_message())
        except (DPClientRuntimeError, StratisCliError) as err:
            if result.propagate:
                raise
            sys.exit("Execution failed: %s" % str(err))
        return 0

    return the_func
