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

import justbytes as jb

from ._error_reporting import handle_error
from ._errors import StratisCliActionError
from ._errors import StratisCliEnvironmentError
from ._parser import gen_parser


def run():
    """
    Generate a function that parses arguments and executes.
    """
    parser = gen_parser()

    # Set default configuration parameters for display of sizes, i.e., values
    # that are generally given in bytes or some multiple thereof.
    jb.Config.set_display_config(jb.DisplayConfig(show_approx_str=False))

    def the_func(command_line_args):
        """
        Run according to the arguments passed.
        """
        result = parser.parse_args(command_line_args)
        try:
            try:
                result.func(result)

            # Keyboard Interrupt is recaught at the outermost possible layer.
            # It is outside the regular execution of the program, so it is
            # handled only there; it is just reraised here.
            # The same holds for SystemExit, except that it must be allowed
            # to propagate to the interpreter, i.e., it should not be recaught
            # anywhere.
            except (KeyboardInterrupt, SystemExit, StratisCliEnvironmentError) as err:
                raise err
            except BaseException as err:
                raise StratisCliActionError(command_line_args, result) from err
        except StratisCliActionError as err:
            if result.propagate:
                raise

            handle_error(err)

        return 0

    return the_func
