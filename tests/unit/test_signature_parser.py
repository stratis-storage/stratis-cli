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
Test signature parsing.
"""


import unittest

import pyparsing

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies

from stratis_cli._dbus._signature._parsing import SignatureParser

SIMPLE_STRATEGY = strategies.sampled_from(
   ['y', 'b', 'n', 'q', 'i', 'u', 'x', 't', 'd', 'h', 's', 'o', 'g', 'v']
)

SINGLETON_SIGNATURE_STRATEGY = strategies.recursive(
   SIMPLE_STRATEGY,
   lambda children: \
      strategies.builds(
         ''.join,
         strategies.lists(children, min_size=1)
      ).flatmap(lambda v: strategies.just('(' + v + ')')) | \
      children.flatmap(lambda v: strategies.just('a' + v)) | \
      strategies.builds(
         lambda x, y: x + y,
         SIMPLE_STRATEGY,
         children
      ).flatmap(lambda v: strategies.just('a' + '{' + v + '}')),
   max_leaves=20
)

SIGNATURE_STRATEGY = strategies.builds(
   ''.join,
   strategies.lists(SINGLETON_SIGNATURE_STRATEGY, max_size=10)
)

class ParseTestCase(unittest.TestCase):
    """
    Test parsing various signatures.
    """

    _PARSER = SignatureParser()

    @given(SIGNATURE_STRATEGY)
    @settings(max_examples=100)
    def testParsing(self, signature):
        """
        Test that parsing is always succesful.
        """
        self.assertIsNotNone(
           self._PARSER.PARSER.parseString(signature, parseAll=True)
        )

    def testExceptions(self):
        """
        Test failure on some invalid strings.
        """
        parser = self._PARSER.PARSER
        with self.assertRaises(pyparsing.ParseException):
            parser.parseString('a', parseAll=True)
        with self.assertRaises(pyparsing.ParseException):
            parser.parseString('()', parseAll=True)
        with self.assertRaises(pyparsing.ParseException):
            parser.parseString('{}', parseAll=True)
        with self.assertRaises(pyparsing.ParseException):
            parser.parseString('{b}', parseAll=True)
        with self.assertRaises(pyparsing.ParseException):
            parser.parseString('a{b}', parseAll=True)
        with self.assertRaises(pyparsing.ParseException):
            parser.parseString('a{}', parseAll=True)
        with self.assertRaises(pyparsing.ParseException):
            parser.parseString('a{byy}', parseAll=True)
        with self.assertRaises(pyparsing.ParseException):
            parser.parseString('a{ayy}', parseAll=True)
