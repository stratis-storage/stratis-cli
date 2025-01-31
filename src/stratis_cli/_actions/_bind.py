# Copyright 2021 Red Hat, Inc.
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
Miscellaneous pool-binding actions.
"""

# isort: STDLIB
import json

from .._constants import EncryptionMethod
from .._errors import StratisCliEngineError, StratisCliNoChangeError
from .._stratisd_constants import (
    CLEVIS_KEY_TANG_TRUST_URL,
    CLEVIS_KEY_THP,
    CLEVIS_KEY_URL,
    CLEVIS_PIN_TANG,
    CLEVIS_PIN_TPM2,
    StratisdErrors,
)
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._utils import ClevisInfo


class BindActions:
    """
    Pool binding actions actions.
    """

    @staticmethod
    def _bind_clevis(namespace, clevis_info):
        """
        Generic bind method. For further information about Clevis, and
        discussion of the pin and the configuration, consult Clevis
        documentation.

        :param ClevisInfo clevis_info: Clevis info
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
        (changed, return_code, return_msg) = Pool.Methods.BindClevis(
            get_object(pool_object_path),
            {
                "pin": clevis_info.pin,
                "json": json.dumps(clevis_info.config),
                "token_slot": (False, 0),
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, return_msg)

        # stratisd does not do idempotency checks when binding with Clevis;
        # because there are multiple token slots, a new Clevis binding will
        # just find the next token slot.
        if not changed:  # pragma: no cover
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

        BindActions._bind_clevis(namespace, ClevisInfo(CLEVIS_PIN_TANG, clevis_config))

    @staticmethod
    def bind_tpm(namespace):
        """
        Bind all devices in an encrypted pool using TPM.

        :raises StratisCliNoChangeError:
        :raises StratisCliEngineError:
        """

        BindActions._bind_clevis(namespace, ClevisInfo(CLEVIS_PIN_TPM2, {}))

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
                "token_slot": (False, 0),
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, return_msg)

        if not changed:
            raise StratisCliNoChangeError("bind", pool_name)

    @staticmethod
    def unbind(namespace):
        """
        Unbind all devices in an encrypted pool.

        :raises StratisCliNoChangeError:
        :raises StratisCliEngineError:
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

        unbind_method = (
            Pool.Methods.UnbindClevis
            if namespace.method is EncryptionMethod.CLEVIS
            else Pool.Methods.UnbindKeyring
        )

        (changed, return_code, return_msg) = unbind_method(
            get_object(pool_object_path),
            {
                "token_slot": (
                    (False, 0)
                    if namespace.token_slot is None
                    else (True, namespace.token_slot)
                )
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, return_msg)

        if not changed:
            raise StratisCliNoChangeError("unbind", pool_name)


class RebindActions:
    """
    Pool rebinding actions
    """

    @staticmethod
    def rebind_clevis(namespace):
        """
        Rebind with Clevis nbde/tang
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

        pool_name = namespace.pool_name

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )
        (changed, return_code, return_msg) = Pool.Methods.RebindClevis(
            get_object(pool_object_path),
            {
                "token_slot": (
                    (False, 0)
                    if namespace.token_slot is None
                    else (True, namespace.token_slot)
                )
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, return_msg)

        if not changed:
            # The sim engine always returns true on a rebind with Clevis
            raise StratisCliNoChangeError("rebind", pool_name)  # pragma: no cover

    @staticmethod
    def rebind_keyring(namespace):
        """
        Rebind with a kernel keyring
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

        pool_name = namespace.pool_name
        keydesc = namespace.keydesc

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props={"Name": pool_name})
            .require_unique_match(True)
            .search(managed_objects)
        )

        (changed, return_code, return_msg) = Pool.Methods.RebindKeyring(
            get_object(pool_object_path),
            {
                "key_desc": keydesc,
                "token_slot": (
                    (False, 0)
                    if namespace.token_slot is None
                    else (True, namespace.token_slot)
                ),
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, return_msg)

        if not changed:
            raise StratisCliNoChangeError("rebind", pool_name)
