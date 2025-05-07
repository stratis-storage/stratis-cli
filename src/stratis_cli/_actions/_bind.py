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

from .._constants import EncryptionMethod, IdType, PoolId
from .._errors import StratisCliEngineError, StratisCliNoChangeError
from .._stratisd_constants import StratisdErrors
from ._connection import get_object
from ._constants import TOP_OBJECT


def _get_pool_id(namespace):
    """
    :return: Id representing how to lookup the pool
    """
    return PoolId(IdType.NAME, namespace.pool_name)


class BindActions:
    """
    Pool binding actions actions.
    """

    @staticmethod
    def bind_clevis(namespace):
        """
        Generic bind method. For further information about Clevis, and
        discussion of the pin and the configuration, consult Clevis
        documentation.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        pool_id = _get_pool_id(namespace)

        (pool_object_path, _) = next(
            pools(props=pool_id.managed_objects_key())
            .require_unique_match(True)
            .search(managed_objects)
        )
        (changed, return_code, return_msg) = Pool.Methods.BindClevis(
            get_object(pool_object_path),
            {
                "pin": namespace.clevis.pin,
                "json": json.dumps(namespace.clevis.config),
                "token_slot": (False, 0),
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, return_msg)

        # stratisd does not do idempotency checks when binding with Clevis;
        # because there are multiple token slots, a new Clevis binding will
        # just find the next token slot.
        if not changed:  # pragma: no cover
            raise StratisCliNoChangeError("bind", pool_id.id_value)

    @staticmethod
    def bind_keyring(namespace):
        """
        Bind all devices in an encrypted pool using the kernel keyring.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        pool_id = _get_pool_id(namespace)

        (pool_object_path, _) = next(
            pools(props=pool_id.managed_objects_key())
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
            raise StratisCliNoChangeError("bind", pool_id.id_value)

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

        pool_id = _get_pool_id(namespace)

        (pool_object_path, _) = next(
            pools(props=pool_id.managed_objects_key())
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
            raise StratisCliNoChangeError("unbind", pool_id.id_value)


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

        pool_id = _get_pool_id(namespace)

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        (pool_object_path, _) = next(
            pools(props=pool_id.managed_objects_key())
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
            raise StratisCliNoChangeError(
                "rebind", pool_id.id_value
            )  # pragma: no cover

    @staticmethod
    def rebind_keyring(namespace):
        """
        Rebind with a kernel keyring
        """
        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, Pool, pools

        keydesc = namespace.keydesc

        proxy = get_object(TOP_OBJECT)
        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})
        pool_id = _get_pool_id(namespace)
        (pool_object_path, _) = next(
            pools(props=pool_id.managed_objects_key())
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
            raise StratisCliNoChangeError("rebind", pool_id.id_value)
