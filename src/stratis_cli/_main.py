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

# isort: THIRDPARTY
import justbytes as jb

from ._error_reporting import handle_error
from ._errors import StratisCliActionError, StratisCliEnvironmentError
from ._exit import StratisCliErrorCodes, exit_
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

        # Use a very specific condition to determine if namespace verification
        # is needed. FIXME: This code should be reviewed if any change is
        # made to how the "pool create" subcommand's options are parsed in
        # case it is made unnecessary by that change.
        # I filed an argparse issue that might address this:
        # https://github.com/python/cpython/issues/114411.
        if (  # pylint: disable=too-many-boolean-expressions
            hasattr(result, "clevis")
            and hasattr(result, "trust_url")
            and hasattr(result, "thumbprint")
            and hasattr(result, "tang_url")
            and "create" in command_line_args
            and "pool" in command_line_args
        ):
            if result.clevis in ("nbde", "tang") and result.tang_url is None:
                exit_(
                    StratisCliErrorCodes.PARSE_ERROR,
                    "Specified binding with Clevis Tang server, but "
                    "URL was not specified. Use --tang-url option to "
                    "specify tang URL.",
                )

            if result.tang_url is not None and (
                not result.trust_url and result.thumbprint is None
            ):
                exit_(
                    StratisCliErrorCodes.PARSE_ERROR,
                    "Specified binding with Clevis Tang server, but "
                    "neither --thumbprint nor --trust-url option was "
                    "specified.",
                )

            if result.tang_url is not None and (
                result.clevis is None or result.clevis not in ("nbde", "tang")
            ):
                exit_(
                    StratisCliErrorCodes.PARSE_ERROR,
                    "Specified --tang-url without specifying Clevis "
                    "encryption method. Use --clevis=tang to choose Clevis "
                    "encryption.",
                )

            if (
                result.trust_url or result.thumbprint is not None
            ) and result.tang_url is None:
                exit_(
                    StratisCliErrorCodes.PARSE_ERROR,
                    "Specified --trust-url or --thumbprint without specifying "
                    "tang URL. Use --tang-url to specify URL.",
                )

        try:
            try:
                result.func(result)

            # Keyboard Interrupt is recaught at the outermost possible layer.
            # It is outside the regular execution of the program, so it is
            # handled only there; it is just reraised here.
            # The same holds for SystemExit, except that it must be allowed
            # to propagate to the interpreter, i.e., it should not be recaught
            # anywhere.
            except (
                BrokenPipeError,
                KeyboardInterrupt,
                SystemExit,
                StratisCliEnvironmentError,
            ) as err:
                raise err
            except BaseException as err:
                raise StratisCliActionError(command_line_args, result) from err
        except StratisCliActionError as err:
            if result.propagate:
                raise

            handle_error(err)

        return 0

    return the_func
