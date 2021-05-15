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
from getpass import getpass

from .._errors import (
    StratisCliEngineError,
    StratisCliIncoherenceError,
    StratisCliKeyfileNotFoundError,
    StratisCliNameConflictError,
    StratisCliNoChangeError,
    StratisCliResourceNotFoundError,
)
from .._stratisd_constants import (
    CLEVIS_KEY_TANG_TRUST_URL,
    CLEVIS_KEY_THP,
    CLEVIS_KEY_URL,
    CLEVIS_PIN_TANG,
    CLEVIS_PIN_TPM2,
    ReportKey,
    StratisdErrors,
)
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._formatting import print_table
from ._utils import fetch_property


def _fetch_keylist_property(proxy):
    """
    Fetch the KeyList property from stratisd.
    :param proxy: proxy to the top object in stratisd
    :return: list of key descriptions
    :rtype: list of str
    :raises StratisCliPropertyNotFoundError:
    :raises StratisCliEnginePropertyError:
    """
    return fetch_property(proxy, "KeyList")


def _add_update_key(proxy, key_desc, capture_key, *, keyfile_path):
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

    # pylint: disable=import-outside-toplevel
    from ._data import Manager

    if capture_key:  # pragma: no cover
        password = getpass(prompt="Enter key data followed by the return key: ")

        (read, write) = os.pipe()
        os.write(write, password.encode("utf-8"))

        file_desc = read
        fd_is_pipe = True
    else:
        try:
            file_desc = os.open(keyfile_path, os.O_RDONLY)
        except FileNotFoundError as err:
            raise StratisCliKeyfileNotFoundError(keyfile_path) from err

        fd_is_pipe = False

    add_ret = Manager.Methods.SetKey(
        proxy,
        {"key_desc": key_desc, "key_fd": file_desc, "interactive": False},
    )

    if fd_is_pipe:  # pragma: no cover
        os.close(write)
    else:
        os.close(file_desc)

    return add_ret


class TopActions:
    """
    Top level actions.
    """

    @staticmethod
    def get_report(namespace):
        """
        Get the requested report from stratisd.

        :raises StratisCliEngineError:
        """

        # pylint: disable=import-outside-toplevel
        if namespace.report_name == str(ReportKey.MANAGED_OBJECTS):

            from ._data import ObjectManager

            json_report = ObjectManager.Methods.GetManagedObjects(
                get_object(TOP_OBJECT), {}
            )

        else:

            if namespace.report_name == str(ReportKey.ENGINE_STATE):

                from ._data import Manager

                (report, return_code, message) = Manager.Methods.EngineStateReport(
                    get_object(TOP_OBJECT), {}
                )

            else:

                from ._data import Report

                (report, return_code, message) = Report.Methods.GetReport(
                    get_object(TOP_OBJECT), {"name": namespace.report_name}
                )

            # The only reason that stratisd has for returning an error code is
            # if the report name is unrecognized. However, the parser restricts
            # the list of names to only the ones that stratisd recognizes, so
            # this branch can only be taken due to an unexpected bug in
            # stratisd.
            if return_code != StratisdErrors.OK:  # pragma: no cover
                raise StratisCliEngineError(return_code, message)

            json_report = json.loads(report)

        json.dump(json_report, sys.stdout, indent=4, sort_keys=True)
        print(file=sys.stdout)

    @staticmethod
    def set_key(namespace):
        """
        Set a key in the kernel keyring.

        :raises StratisCliEngineError:
        :raises StratisCliEnginePropertyError:
        :raises StratisCliPropertyNotFoundError:
        :raises StratisCliNameConflictError:
        :raises StratisCliIncoherenceError:
        """
        proxy = get_object(TOP_OBJECT)

        key_list = _fetch_keylist_property(proxy)
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
                    "Key %s was reported to not exist but stratisd reported "
                    "that no change was made to the key"
                )
                % namespace.keydesc
            )

        # A key was updated even though there was no key reported to already exist.
        if changed and existing_modified:  # pragma: no cover
            raise StratisCliIncoherenceError(
                (
                    "Key %s was reported to not exist but stratisd reported "
                    "that it reset an existing key"
                )
                % namespace.keydesc
            )

    @staticmethod
    def reset_key(namespace):
        """
        Reset the key data for an existing key in the kernel keyring.

        :raises StratisCliEngineError:
        :raises StratisCliEnginePropertyError:
        :raises StratisCliResourceNotFoundError:
        :raises StratisCliPropertyNotFoundError:
        :raises StratisCliIncoherenceError:
        """
        proxy = get_object(TOP_OBJECT)

        key_list = _fetch_keylist_property(proxy)
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
                    "Key %s was reported to already exist but stratisd reported "
                    "that it created a new key"
                )
                % namespace.keydesc
            )

    @staticmethod
    def unset_key(namespace):
        """
        Unset a key in kernel keyring.

        :raises StratisCliEngineError:
        :raises StratisCliEnginePropertyError:
        :raises StratisCliPropertyNotFoundError:
        :raises StratisCliNoChangeError:
        :raises StratisCliIncoherenceError:
        """
        # pylint: disable=import-outside-toplevel
        from ._data import Manager

        proxy = get_object(TOP_OBJECT)

        key_list = _fetch_keylist_property(proxy)
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
                    "Key %s was reported to exist but stratisd reported "
                    "that no key was unset"
                )
                % namespace.keydesc
            )

    @staticmethod
    def list_keys(_):
        """
        List keys in kernel keyring.

        :raises StratisCliPropertyNotFoundError:
        :raises StratisCliEnginePropertyError:
        """
        proxy = get_object(TOP_OBJECT)

        key_list = [[key_desc] for key_desc in _fetch_keylist_property(proxy)]

        print_table(
            ["Key Description"], sorted(key_list, key=lambda entry: entry[0]), ["<"]
        )

    @staticmethod
    def _bind_clevis(namespace, clevis_pin, clevis_config):
        """
        Generic bind method. For further information about Clevis, and
        discussion of the pin and the configuration, consult Clevis
        documentation.

        :param str clevis_pin: Clevis pin
        :param dict clevis_config: configuration, may contain Stratis keys
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        pool_name = namespace.pool_name
        (pool_object_path, _) = next(
            pools(props={"Name": pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )
        (changed, return_code, return_msg) = Pool.Methods.Bind(
            get_object(pool_object_path),
            {
                "pin": clevis_pin,
                "json": json.dumps(clevis_config),
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, return_msg)

        if not changed:
            raise StratisCliNoChangeError("bind", pool_name)

    @staticmethod
    def bind_tang(namespace):
        """
        Bind all devices in an encrypted pool using the specified tang server.

        :raises StratisCliNoChangeError:
        :raises StratisCliEngineError:
        """
        clevis_config = {CLEVIS_KEY_URL: namespace.url}
        if namespace.trust_url:
            clevis_config[CLEVIS_KEY_TANG_TRUST_URL] = True
        else:
            assert namespace.thumbprint is not None
            clevis_config[CLEVIS_KEY_THP] = namespace.thumbprint

        TopActions._bind_clevis(namespace, CLEVIS_PIN_TANG, clevis_config)

    @staticmethod
    def bind_tpm(namespace):
        """
        Bind all devices in an encrypted pool using TPM.

        :raises StratisCliNoChangeError:
        :raises StratisCliEngineError:
        """

        TopActions._bind_clevis(namespace, CLEVIS_PIN_TPM2, {})

    @staticmethod
    def bind_keyring(namespace):
        """
        Bind all devices in an encrypted pool using the kernel keyring.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        pool_name = namespace.pool_name
        (pool_object_path, _) = next(
            pools(props={"Name": pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )
        (changed, return_code, return_msg) = Pool.Methods.BindKeyring(
            get_object(pool_object_path),
            {
                "key_desc": namespace.keydesc,
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, return_msg)

        if not changed:
            raise StratisCliNoChangeError("bind", pool_name)
