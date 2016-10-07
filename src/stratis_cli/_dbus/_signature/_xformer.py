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
Transforming Python basic types to Python dbus types.
"""

import dbus
import functools

from dbus_signature_pyparsing import Parser

from ..._errors import StratisCliValueError


class ToDbusXformer(Parser):
    """
    Class which extends a Parser to yield a function that yields
    a function that transforms a value in base Python types to a correct value
    using dbus-python types.

    Actually, it yields a pair, a function and a signature string. The
    signature string is useful for stowing a signature in Array or Dictionary
    types, as may be necessary if the Array or Dictionary is empty, and so
    the type can not be inferred from the contents of the value.
    """
    # pylint: disable=too-few-public-methods

    @staticmethod
    def _handleArray(toks):
        """
        Generate the correct function for an array signature.

        :param toks: the list of parsed tokens
        :returns: function that returns an Array or Dictionary value
        :rtype: (or list dict) -> ((or Array Dictionary) * str)
        """

        if len(toks) == 5 and toks[1] == '{' and toks[4] == '}':
            subtree = toks[2:4]
            signature = ''.join(s for (_, s) in subtree)
            [key_func, value_func] = [f for (f, _) in subtree]

            def the_func(a_dict):
                """
                Function for generating a Dictionary from a dict.

                :param a_dict: the dictionary to transform
                :type a_dict: dict of (`a * `b)

                :returns: a dbus dictionary of transformed values
                :rtype: Dictionary
                """
                return dbus.types.Dictionary(
                    [(key_func(x), value_func(y)) for (x, y) in a_dict.items()],
                    signature
                )

            return (the_func, 'a{' + signature + '}')

        elif len(toks) == 2:

            (func, sig) = toks[1]

            def the_func(a_list):
                """
                Function for generating an Array from a list.

                :param a_list: the list to transform
                :type a_list: list of `a
                :returns: a dbus Array of transformed values
                :rtype: Array
                """

                return dbus.types.Array([func(x) for x in a_list], sig)

            return (the_func, 'a' + sig)

        else: # pragma: no cover
            raise StratisCliValueError(toks, "toks", "unexpected tokens")

    @staticmethod
    def _handleStruct(toks):
        """
        Generate the correct function for a struct signature.

        :param toks: the list of parsed tokens
        :returns: function that returns an Array or Dictionary value
        :rtype: list -> (Struct * str)
        """
        subtrees = toks[1:-1]
        signature = ''.join(s for (_, s) in subtrees)
        funcs = [f for (f, _) in subtrees]

        def the_func(a_list):
            """
            Function for generating a Struct from a list.

            :param a_list: the list to transform
            :type a_list: list of `a
            :returns: a dbus Struct of transformed values
            :rtype: Struct
            """
            return dbus.types.Struct(f(x) for (f, x) in zip(funcs, a_list))

        return (the_func, '(' + signature + ')')

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
            raise StratisCliValueError(s, "the string being parsed", message)

        return raises

    def __init__(self):
        super(ToDbusXformer, self).__init__()

        self.BYTE.setParseAction(lambda: (dbus.types.Byte, 'y'))
        self.BOOLEAN.setParseAction(lambda: (dbus.types.Boolean, 'b'))
        self.INT16.setParseAction(lambda: (dbus.types.Int16, 'n'))
        self.UINT16.setParseAction(lambda: (dbus.types.UInt16, 'q'))
        self.INT32.setParseAction(lambda: (dbus.types.Int32, 'i'))
        self.UINT32.setParseAction(lambda: (dbus.types.UInt32, 'u'))
        self.INT64.setParseAction(lambda: (dbus.types.Int64, 'x'))
        self.UINT64.setParseAction(lambda: (dbus.types.UInt64, 't'))
        self.DOUBLE.setParseAction(lambda: (dbus.types.Double, 'd'))
        self.UNIX_FD.setParseAction(lambda: (dbus.types.UnixFd, 'h'))

        self.STRING.setParseAction(lambda: (dbus.types.String, 's'))
        self.OBJECT_PATH.setParseAction(lambda: (dbus.types.ObjectPath, 'o'))
        self.SIGNATURE.setParseAction(lambda: (dbus.types.Signature, 'g'))

        self.VARIANT.setParseAction(
           ToDbusXformer._raiseException("Unhandled variant signature.")
        )

        self.ARRAY.setParseAction(ToDbusXformer._handleArray)

        self.STRUCT.setParseAction(ToDbusXformer._handleStruct)


class Decorators(object):
    """
    Dbus signature based method decorators.

    These decorate the method to transform its arguments and return values.
    """
    # pylint: disable=too-few-public-methods

    _PARSER = ToDbusXformer().PARSER


    @staticmethod
    def in_decorator(signature):
        """
        Generates a decorator that transforms input arguments.

        :param str signature: the input signature of the function
        """
        xformers = [
           x for (x, _) in \
              Decorators._PARSER.parseString(signature, parseAll=True)
        ]

        def function_func(func):
            """
            The actual decorator.
            """

            @functools.wraps(func)
            def the_func(self, *args):
                """
                The resulting function.

                Transform each value in args before passing it to func.
                """
                xformed_args = [f(x) for (f, x) in zip(xformers, args)]
                return func(self, *xformed_args)

            return the_func

        return function_func
