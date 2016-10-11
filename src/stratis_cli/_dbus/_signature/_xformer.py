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
    def _variant_levels(level, variant):
        """
        Gets the level for the variant.

        :param int level: the current variant level
        :param bool variant: whether to mark this as a variant

        :returns: a level for the object and one for the function
        :rtype: int * int
        """
        return (level + 1, level + 1) if variant else (0, level)

    def _handleVariant(self):
        """
        Generate the correct function for a variant signature.

        :returns: function that returns an appropriate value
        :rtype: tuple of str * object -> object
        """

        def the_func(a_tuple, variant=False):
            """
            Function for generating a variant value from a tuple.

            :param a_tuple: the parts of the variant
            :type a_tuple: str * object
            :param bool variant: whether the object is a variant
            :returns: a value of the correct type with correct variant level
            :rtype: object * int
            """
            # pylint: disable=unused-argument
            (signature, an_obj) = a_tuple
            (func, sig) = self.COMPLETE.parseString(signature)[0]
            assert sig == signature
            (xformed, _) = func(an_obj, variant=True)
            return (xformed, xformed.variant_level)

        return (the_func, 'v')

    @staticmethod
    def _handleArray(toks):
        """
        Generate the correct function for an array signature.

        :param toks: the list of parsed tokens
        :returns: function that returns an Array or Dictionary value
        :rtype: ((or list dict) -> ((or Array Dictionary) * int)) * str
        """

        if len(toks) == 5 and toks[1] == '{' and toks[4] == '}':
            subtree = toks[2:4]
            signature = ''.join(s for (_, s) in subtree)
            [key_func, value_func] = [f for (f, _) in subtree]

            def the_func(a_dict, variant=False):
                """
                Function for generating a Dictionary from a dict.

                :param a_dict: the dictionary to transform
                :type a_dict: dict of (`a * `b)
                :param bool variant: whether to make the object a variant

                :returns: a dbus dictionary of transformed values and level
                :rtype: Dictionary * int
                """
                elements = \
                   [(key_func(x), value_func(y)) for (x, y) in a_dict.items()]
                level = \
                   0 if elements == [] \
                   else max(max(x, y) for ((_, x), (_, y)) in elements)
                (obj_level, func_level) = \
                   ToDbusXformer._variant_levels(level, variant)
                return (
                   dbus.types.Dictionary(
                      ((x, y) for ((x, _), (y, _)) in elements),
                      signature=signature,
                      variant_level=obj_level
                   ),
                   func_level
                )

            return (the_func, 'a{' + signature + '}')

        elif len(toks) == 2:

            (func, sig) = toks[1]

            def the_func(a_list, variant=False):
                """
                Function for generating an Array from a list.

                :param a_list: the list to transform
                :type a_list: list of `a
                :param bool variant: whether the object is a variant
                :returns: a dbus Array of transformed values and variant level
                :rtype: Array * int
                """
                elements = [func(x) for x in a_list]
                level = 0 if elements == [] else max(x for (_, x) in elements)
                (obj_level, func_level) = \
                   ToDbusXformer._variant_levels(level, variant)

                return (
                   dbus.types.Array(
                      (x for (x, _) in elements),
                      signature=sig,
                      variant_level=obj_level
                   ),
                   func_level
                )

            return (the_func, 'a' + sig)

        else: # pragma: no cover
            raise StratisCliValueError(toks, "toks", "unexpected tokens")

    @staticmethod
    def _handleStruct(toks):
        """
        Generate the correct function for a struct signature.

        :param toks: the list of parsed tokens
        :returns: function that returns an Array or Dictionary value
        :rtype: (list -> (Struct * int)) * str
        """
        subtrees = toks[1:-1]
        signature = ''.join(s for (_, s) in subtrees)
        funcs = [f for (f, _) in subtrees]

        def the_func(a_list, variant=False):
            """
            Function for generating a Struct from a list.

            :param a_list: the list to transform
            :type a_list: list of `a
            :param bool variant: whether to make this object a variant
            :returns: a dbus Struct of transformed values and variant level
            :rtype: Struct * int
            """
            elements = [f(x) for (f, x) in zip(funcs, a_list)]
            level = 0 if elements == [] else max(x for (_, x) in elements)
            (obj_level, func_level) = \
                ToDbusXformer._variant_levels(level, variant)
            return (
               dbus.types.Struct(
                  (x for (x, _) in elements),
                  variant_level=obj_level
               ),
               func_level
            )

        return (the_func, '(' + signature + ')')

    @staticmethod
    def _handleBaseCase(klass, symbol):
        """
        Handle a base case.

        :param type klass: the class constructor
        :param str symbol: the type code
        """
        def the_func(v, variant=False):
            """
            Base case.

            :param bool variant: whether to make this object a variant
            :returns: a tuple of a dbus object and the variant level
            :rtype: dbus object * int
            """
            (obj_level, func_level) = ToDbusXformer._variant_levels(0, variant)
            return (klass(v, variant_level=obj_level), func_level)

        return lambda: (the_func, symbol)

    def __init__(self):
        super(ToDbusXformer, self).__init__()

        self.BYTE.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.Byte, 'y')
        )
        self.BOOLEAN.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.Boolean, 'b')
        )
        self.INT16.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.Int16, 'n')
        )
        self.UINT16.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.UInt16, 'q')
        )
        self.INT32.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.Int32, 'i')
        )
        self.UINT32.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.UInt32, 'u')
        )
        self.INT64.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.Int64, 'x')
        )
        self.UINT64.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.UInt64, 't')
        )
        self.DOUBLE.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.Double, 'd')
        )
        self.UNIX_FD.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.UnixFd, 'h')
        )
        self.STRING.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.String, 's')
        )
        self.OBJECT_PATH.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.ObjectPath, 'o')
        )
        self.SIGNATURE.setParseAction(
           ToDbusXformer._handleBaseCase(dbus.types.Signature, 'g')
        )

        self.VARIANT.setParseAction(self._handleVariant)

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

            def the_func(self, *args):
                """
                The resulting function.

                Transform each value in args before passing it to func.
                """
                xformed = [f(x) for (f, x) in zip(xformers, args)]
                xformed_args = [x for (x, _) in xformed]
                return func(self, *xformed_args)

            return the_func

        return function_func
