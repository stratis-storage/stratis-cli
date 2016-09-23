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
pyparsing based module for parsing a dbus method input or output signature.
"""

from pyparsing import Forward
from pyparsing import Literal
from pyparsing import OneOrMore


class SignatureParser(object):
    """
    Parse a dbus signature using pyparsing.
    """
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods

    def __init__(self):
        """
        Initializer.

        Instantiates the entire parser.

        All productions are public instance attributes.
        """
        self.BYTE = Literal('y')('BYTE')
        self.BOOLEAN = Literal('b')('BOOLEAN')
        self.INT16 = Literal('n')('INT16')
        self.UINT16 = Literal('q')('UINT16')
        self.INT32 = Literal('i')('INT32')
        self.UINT32 = Literal('u')('UINT32')
        self.INT64 = Literal('x')('INT64')
        self.UINT64 = Literal('t')('UINT64')
        self.DOUBLE = Literal('d')('DOUBLE')
        self.UNIX_FD = Literal('h')('UNIX_FD')

        self.STRING = Literal('s')('STRING')
        self.OBJECT_PATH = Literal('o')('OBJECT_PATH')
        self.SIGNATURE = Literal('g')('SIGNATURE')

        self.VARIANT = Literal('v')('VARIANT')

        simple = \
           self.BYTE ^ \
           self.BOOLEAN ^ \
           self.DOUBLE ^ \
           self.INT16 ^ \
           self.UINT16 ^ \
           self.INT32 ^ \
           self.UINT32 ^ \
           self.INT64 ^ \
           self.UINT64 ^ \
           self.UNIX_FD ^ \
           self.STRING ^ \
           self.OBJECT_PATH ^ \
           self.SIGNATURE ^ \
           self.VARIANT

        self.TREE = Forward()

        self.DICT_ENTRY = \
           Literal('{') + \
           simple + \
           Forward(self.TREE) + \
           Literal('}')
        self.DICT_ENTRY.setName('DICT_ENTRY')

        self.ARRAY = Literal('a') + (Forward(self.TREE) ^ self.DICT_ENTRY)
        self.ARRAY.setName('ARRAY')

        self.STRUCT = \
           Literal('(') + OneOrMore(Forward(self.TREE)) + Literal(')')
        self.STRUCT.setName('STRUCT')

        self.TREE <<= simple ^ self.ARRAY ^ self.STRUCT
        self.PARSER = OneOrMore(self.TREE)
