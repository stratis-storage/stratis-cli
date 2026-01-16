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
Miscellaneous top-level actions.
"""

# isort: STDLIB
import json
import os
import sys
from argparse import Namespace
from typing import Tuple

# isort: THIRDPARTY
from dbus import Array, Dictionary, String, Struct, UInt16
from dbus.proxies import ProxyObject

from .._errors import (
    StratisCliEngineError,
    StratisCliIncoherenceError,
    StratisCliNameConflictError,
    StratisCliNoChangeError,
    StratisCliResourceNotFoundError,
)
from .._stratisd_constants import ReportKey, StratisdErrors
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import print_table
from ._utils import get_passphrase_fd


def _fetch_keylist(proxy: ProxyObject) -> Array:
    """
    Fetch the list of Stratis keys from stratisd.
    :param proxy: proxy to the top object in stratisd
    :return: list of key descriptions
    :rtype: list of str
    :raises StratisCliEngineError:
    """
    from ._data import MANAGER_GEN  # pylint: disable=import-outside-toplevel

    Manager = MANAGER_GEN.make_partial_class(  # pylint: disable=invalid-name
        methods=["ListKeys"], properties=[]
    )

    (keys, return_code, message) = Manager.Methods.ListKeys(proxy, {})
    if return_code != StratisdErrors.OK:  # pragma: no cover
        raise StratisCliEngineError(return_code, message)
    return keys


def _add_update_key(
    proxy: ProxyObject, key_desc: str, capture_key: bool, *, keyfile_path
) -> Tuple[Struct, UInt16, String]:
    """
    Issue a command to set or reset a key in the kernel keyring with the option
    to set it interactively or from a keyfile.

    :param proxy: proxy to the top object
    :param str key_desc: key description for the key to be set or reset
    :param bool capture_key: whether the key setting should be interactive
    :param keyfile_path: optional path to the keyfile containing the key
    :type keyfile_path: str or NoneType
    :return: the result of the SetKey D-Bus call
    :rtype: D-Bus types (bb), q, and s
    """
    assert capture_key == (keyfile_path is None)

    fd_argument, fd_to_close = get_passphrase_fd(keyfile_path=keyfile_path)

    from ._data import MANAGER_GEN  # pylint: disable=import-outside-toplevel

    Manager = MANAGER_GEN.make_partial_class(  # pylint: disable=invalid-name
        methods=["SetKey"], properties=[]
    )

    add_ret = Manager.Methods.SetKey(
        proxy,
        {"key_desc": key_desc, "key_fd": fd_argument},
    )

    os.close(fd_to_close)

    return add_ret


class TopActions:
    """
    Top level actions.
    """

    @staticmethod
    def get_report(namespace: Namespace):
        """
        Get the requested report from stratisd.

        :raises StratisCliEngineError:
        """

        if namespace.report_name is ReportKey.MANAGED_OBJECTS:
            from ._data import ObjectManager  # pylint: disable=import-outside-toplevel

            dbus_report: Dictionary = ObjectManager.Methods.GetManagedObjects(
                get_object(TOP_OBJECT), {}
            )

            # unlike pprint, json.dump prints GetManagedObjects result nicely
            json.dump(
                dbus_report,
                sys.stdout,
                indent=4,
                sort_keys=(not namespace.no_sort_keys),
            )

        else:
            if namespace.report_name is ReportKey.ENGINE_STATE:
                from ._data import (  # pylint: disable=import-outside-toplevel
                    MANAGER_GEN,
                )

                Manager = (  # pylint: disable=invalid-name
                    MANAGER_GEN.make_partial_class(
                        methods=["EngineStateReport"], properties=[]
                    )
                )

                (json_report, return_code, message) = Manager.Methods.EngineStateReport(
                    get_object(TOP_OBJECT), {}
                )

            else:
                from ._data import REPORT_GEN  # pylint: disable=import-outside-toplevel

                Report = REPORT_GEN.make_partial_class()  # pylint: disable=invalid-name

                (json_report, return_code, message) = Report.Methods.GetReport(
                    get_object(TOP_OBJECT), {"name": str(namespace.report_name)}
                )

            # The only reason that stratisd has for returning an error code is
            # if the report name is unrecognized. However, the parser restricts
            # the list of names to only the ones that stratisd recognizes, so
            # this branch can only be taken due to an unexpected bug in
            # stratisd.
            if return_code != StratisdErrors.OK:  # pragma: no cover
                raise StratisCliEngineError(return_code, message)

            json.dump(
                json.loads(json_report),
                sys.stdout,
                indent=4,
                sort_keys=(not namespace.no_sort_keys),
            )

        print(file=sys.stdout)

    @staticmethod
    def set_key(namespace: Namespace):
        """
        Set a key in the kernel keyring.

        :raises StratisCliEngineError:
        :raises StratisCliNameConflictError:
        :raises StratisCliIncoherenceError:
        """
        proxy = get_object(TOP_OBJECT)

        key_list = _fetch_keylist(proxy)
        if namespace.keydesc in key_list:
            raise StratisCliNameConflictError("key", namespace.keydesc)

        ((changed, existing_modified), return_code, message) = _add_update_key(
            proxy,
            namespace.keydesc,
            namespace.capture_key,
            keyfile_path=namespace.keyfile_path,
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        if not changed and not existing_modified:  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    f"Key {namespace.keydesc} was reported to not exist but stratisd reported "
                    f"that no change was made to the key"
                )
            )

        # A key was updated even though there was no key reported to already exist.
        if changed and existing_modified:  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    f"Key {namespace.keydesc} was reported to not exist but stratisd reported "
                    f"that it reset an existing key"
                )
            )

    @staticmethod
    def reset_key(namespace: Namespace):
        """
        Reset the key data for an existing key in the kernel keyring.

        :raises StratisCliEngineError:
        :raises StratisCliResourceNotFoundError:
        :raises StratisCliIncoherenceError:
        """
        proxy = get_object(TOP_OBJECT)

        key_list = _fetch_keylist(proxy)
        if namespace.keydesc not in key_list:
            raise StratisCliResourceNotFoundError("reset", namespace.keydesc)

        ((changed, existing_modified), return_code, message) = _add_update_key(
            proxy,
            namespace.keydesc,
            namespace.capture_key,
            keyfile_path=namespace.keyfile_path,
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        # The key description existed and the key was not changed.
        if not changed and not existing_modified:
            raise StratisCliNoChangeError("reset", namespace.keydesc)

        # A new key was added even though there was a key reported to already exist.
        if changed and not existing_modified:  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    f"Key {namespace.keydesc} was reported to already exist but stratisd reported "
                    f"that it created a new key"
                )
            )

    @staticmethod
    def unset_key(namespace: Namespace):
        """
        Unset a key in kernel keyring.

        :raises StratisCliEngineError:
        :raises StratisCliNoChangeError:
        :raises StratisCliIncoherenceError:
        """
        from ._data import MANAGER_GEN  # pylint: disable=import-outside-toplevel

        Manager = MANAGER_GEN.make_partial_class(  # pylint: disable=invalid-name
            methods=["UnsetKey"], properties=[]
        )

        proxy = get_object(TOP_OBJECT)

        key_list = _fetch_keylist(proxy)
        if namespace.keydesc not in key_list:
            raise StratisCliNoChangeError("remove", namespace.keydesc)

        (changed, return_code, message) = Manager.Methods.UnsetKey(
            proxy, {"key_desc": namespace.keydesc}
        )

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if not changed:  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    f"Key {namespace.keydesc} was reported to exist but stratisd reported "
                    f"that no key was unset"
                )
            )

    @staticmethod
    def list_keys(_: Namespace):
        """
        List keys in kernel keyring.

        :raises StratisCliEngineError:
        """
        proxy = get_object(TOP_OBJECT)

        key_list = [[key_desc] for key_desc in _fetch_keylist(proxy)]

        print_table(
            ["Key Description"], sorted(key_list, key=lambda entry: entry[0]), ["<"]
        )
