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

from into_dbus_python import xformer


class Decorators(object):
    """
    Dbus signature based method decorators.

    These decorate the method to transform its arguments and return values.
    """
    # pylint: disable=too-few-public-methods

    @staticmethod
    def in_decorator(signature):
        """
        Generates a decorator that transforms input arguments.

        :param str signature: the input signature of the function
        """
        xformer_func = xformer(signature)

        def function_func(func):
            """
            The actual decorator.
            """

            def the_func(self, *args):
                """
                The resulting function.

                Transform each value in args before passing it to func.
                """
                xformed_args = xformer_func(args)
                return func(self, *xformed_args)

            return the_func

        return function_func
