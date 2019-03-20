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

import dbus

from dbus_client_gen import DbusClientRuntimeError
from dbus_python_client_gen import DPClientRuntimeError

from ._errors import StratisCliActionError
from ._errors import StratisCliRuntimeError
from ._error_reporting import handle_error
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
            try:
                result.func(result)
            except (dbus.exceptions.DBusException, AttributeError,
                    DbusClientRuntimeError, DPClientRuntimeError,
                    StratisCliRuntimeError) as err:
                raise StratisCliActionError(command_line_args, result) from err
        except StratisCliActionError as err:
            if result.propagate:
                raise

            handle_error(err)

        return 0

    return the_func
