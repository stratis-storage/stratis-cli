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

import string
import unittest

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies

from stratis_cli._dbus._signature._parsing import SignatureParser
from stratis_cli._dbus._signature._xformer import ToDbusXformer

# Omits v, variant since xformer does not handle variants.
# Omits h, unix fd, because it is unclear what are valid fds for dbus
SIMPLE_STRATEGY = strategies.sampled_from(
   ['y', 'b', 'n', 'q', 'i', 'u', 'x', 't', 'd', 's', 'o', 'g']
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
   strategies.lists(SINGLETON_SIGNATURE_STRATEGY, min_size=1, max_size=10)
)

OBJECT_PATH_STRATEGY = strategies.one_of(
   strategies.builds(
      '/'.__add__,
      strategies.builds(
         '/'.join,
         strategies.lists(
            strategies.text(
               alphabet=[
                  x for x in \
                     string.digits + \
                     string.ascii_uppercase + \
                     string.ascii_lowercase + \
                     '_'
               ],
               min_size=1,
               max_size=10
            ),
            max_size=10
         )
      )
   )
)


class StrategyGenerator(SignatureParser):
    """
    Generate a hypothesis strategy for generating objects for a particular
    dbus signature which make use of base Python classes.
    """
    # pylint: disable=too-few-public-methods

    @staticmethod
    def _raiseException(message):
        """
        Handy method yielding a function for raising an exception.

        :param str message: the message
        """
        def raises(s, loc, toks):
            """
            The exception raising method.

            :param str s: the string being parsed
            :param loc: the location of the matching substring
            :param toks: the tokens matched
            """
            # pylint: disable=unused-argument
            raise ValueError(s, "the string being parsed", message)

        return raises

    @staticmethod
    def _handleArray(toks):
        """
        Generate the correct strategy for an array signature.

        :param toks: the list of parsed tokens
        :returns: strategy that generates an array or dict as appropriate
        :rtype: strategy
        """

        if len(toks) == 5 and toks[1] == '{' and toks[4] == '}':
            return strategies.dictionaries(keys=toks[2], values=toks[3])
        elif len(toks) == 2:
            return strategies.lists(elements=toks[1])
        else: # pragma: no cover
            raise ValueError("unexpected tokens")

    def __init__(self):
        super(StrategyGenerator, self).__init__()

        # pylint: disable=unnecessary-lambda
        self.BYTE.setParseAction(
           lambda: strategies.integers(min_value=0, max_value=255)
        )
        self.BOOLEAN.setParseAction(lambda: strategies.booleans())
        self.INT16.setParseAction(
           lambda: strategies.integers(min_value=-0x8000, max_value=0x7fff)
        )
        self.UINT16.setParseAction(
           lambda: strategies.integers(min_value=0, max_value=0xffff)
        )
        self.INT32.setParseAction(
           lambda: strategies.integers(
              min_value=-0x80000000,
              max_value=0x7fffffff
           )
        )
        self.UINT32.setParseAction(
           lambda: strategies.integers(min_value=0, max_value=0xffffffff)
        )
        self.INT64.setParseAction(
           lambda: strategies.integers(
              min_value=-0x8000000000000000,
              max_value=0x7fffffffffffffff
           )
        )
        self.UINT64.setParseAction(
           lambda: strategies.integers(
              min_value=0,
              max_value=0xffffffffffffffff
           )
        )
        self.DOUBLE.setParseAction(lambda: strategies.floats())

        self.STRING.setParseAction(lambda: strategies.text())
        self.OBJECT_PATH.setParseAction(lambda: OBJECT_PATH_STRATEGY)
        self.SIGNATURE.setParseAction(lambda: SIGNATURE_STRATEGY)

        self.VARIANT.setParseAction(
           StrategyGenerator._raiseException("Unhandled variant signature.")
        )

        self.ARRAY.setParseAction(StrategyGenerator._handleArray)

        self.STRUCT.setParseAction(
           # pylint: disable=used-before-assignment
           lambda toks: strategies.tuples(*toks[1:-1])
        )

STRATEGY_GENERATOR = StrategyGenerator().PARSER


class ParseTestCase(unittest.TestCase):
    """
    Test parsing various signatures.
    """

    _PARSER = ToDbusXformer()

    @given(SIGNATURE_STRATEGY)
    @settings(max_examples=100)
    def testParsing(self, signature):
        """
        Test that parsing is always succesful.
        """
        base_type_objects = \
           [x.example() for x in STRATEGY_GENERATOR.parseString(signature)]
        funcs = [f for (f, _) in self._PARSER.PARSER.parseString(signature)]
        self.assertIsNotNone([f(x) for (f, x) in zip(funcs, base_type_objects)])
