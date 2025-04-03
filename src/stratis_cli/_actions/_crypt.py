# Copyright 2025 Red Hat, Inc.
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
Miscellaneous whole pool encryption actions.
"""

# isort: STDLIB
import json

from .._constants import PoolId
from .._errors import (
    StratisCliEngineError,
    StratisCliIncoherenceError,
    StratisCliNoChangeError,
    StratisCliResourceNotFoundError,
    StratisdErrors,
)
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._utils import ClevisInfo


class CryptActions:
    """
    Whole pool encryption actions.
    """

    @staticmethod
    def encrypt(namespace):
        """
        Encrypt a previously unencrypted pool.
        """

        # pylint: disable=import-outside-toplevel
        from ._data import MOPool, ObjectManager, Pool, pools

        pool_id = PoolId.from_parser_namespace(namespace)
        assert pool_id is not None

        proxy = get_object(TOP_OBJECT)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, mopool) = next(
            pools(props=pool_id.managed_objects_key())
            .require_unique_match(True)
            .search(managed_objects)
        )

        if bool(MOPool(mopool).Encrypted()):
            raise StratisCliNoChangeError("encryption on", pool_id)

        clevis_info = (
            None if namespace.clevis is None else ClevisInfo.get_info(namespace.clevis)
        )

        (changed, return_code, message) = Pool.Methods.EncryptPool(
            get_object(pool_object_path),
            pool_id.dbus_args()
            | {
                "key_desc": (
                    []
                    if namespace.key_desc is None
                    else [((False, 0), namespace.key_desc)]
                ),
                "clevis_info": (
                    []
                    if clevis_info is None
                    else [((False, 0), clevis_info.pin, json.dumps(clevis_info.config))]
                ),
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        if not changed:
            raise StratisCliIncoherenceError(
                "Expected to change {pool_id} encryption status to "
                "encrypted, but stratisd reports that it did not change "
                "the encryption status"
            )

    @staticmethod
    def unencrypt(namespace):
        """
        Unencrypt a previously encrypted pool.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MOPool, ObjectManager, Pool, pools

        pool_id = PoolId.from_parser_namespace(namespace)
        assert pool_id is not None

        proxy = get_object(TOP_OBJECT)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, mopool) = next(
            pools(props=pool_id.managed_objects_key())
            .require_unique_match(True)
            .search(managed_objects)
        )

        if not bool(MOPool(mopool).Encrypted()):
            raise StratisCliNoChangeError("encryption off", pool_id)

        (changed, return_code, message) = Pool.Methods.DecryptPool(
            get_object(pool_object_path), {}
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        if not changed:  # pragma: no cover
            raise StratisCliIncoherenceError(
                "Expected to change the pool's encryption status to "
                "unencrypted, but stratisd reports that it did not change "
                "the pool's encryption status"
            )

    @staticmethod
    def reencrypt(namespace):
        """
        Reencrypt an already encrypted pool with a new key.
        """
        # pylint: disable=import-outside-toplevel
        from ._data import MOPool, ObjectManager, Pool, pools

        pool_id = PoolId.from_parser_namespace(namespace)
        assert pool_id is not None

        proxy = get_object(TOP_OBJECT)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, mopool) = next(
            pools(props=pool_id.managed_objects_key())
            .require_unique_match(True)
            .search(managed_objects)
        )

        if not bool(MOPool(mopool).Encrypted()):
            raise StratisCliResourceNotFoundError("reencrypt", "encryption")

        (changed, return_code, message) = Pool.Methods.ReencryptPool(
            get_object(pool_object_path), {}
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        if not changed:
            raise StratisCliIncoherenceError(
                "Expected to reencrypt the pool with a new key but stratisd "
                "reports that it did not change perform the operation"
            )
