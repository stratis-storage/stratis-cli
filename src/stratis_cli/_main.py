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

from ._parser import gen_parser

def run(command_line_args):
    """
    Run according to the arguments passed.
    """
    parser = gen_parser()
    result = parser.parse_args(command_line_args)
    yield result
    if result.subparser_name is None:
        parser.print_help()
    else:
        result.func(result)
    yield 0
