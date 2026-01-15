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
import xml.etree.ElementTree as ET  # nosec B405
from argparse import Namespace

# isort: FIRSTPARTY
from dbus_python_client_gen import make_class

from .._constants import PoolId
from .._errors import (
    StratisCliEngineError,
    StratisCliIncoherenceError,
    StratisCliInPlaceNotSpecified,
    StratisCliNoChangeError,
)
from .._stratisd_constants import StratisdErrors
from ._connection import get_object
from ._constants import TOP_OBJECT
from ._utils import long_running_operation


def _make_class(spec, class_name, *, methods=None, timeout=-1):
    """
    Make a class from spec, with only requested methods.
    Interpret None as all methods.
    """
    new_spec = ET.Element(spec.tag, spec.attrib)
    new_spec.extend(
        [
            child
            for child in spec
            if child.tag == "method" and methods is None or child.get("name") in methods
        ]
    )
    return make_class(class_name, new_spec, timeout=timeout)


class CryptActions:
    """
    Whole pool encryption actions.
    """

    @staticmethod
    @long_running_operation
    def encrypt(namespace: Namespace):
        """
        Encrypt a previously unencrypted pool.
        """

        if not namespace.in_place:
            raise StratisCliInPlaceNotSpecified()

        # pylint: disable=import-outside-toplevel
        from ._data import MOPool, ObjectManager, pool_spec, pools

        Pool = _make_class(  # pylint: disable=invalid-name
            pool_spec, "Pool", methods=["EncryptPool"], timeout=10
        )

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

        (changed, return_code, message) = Pool.Methods.EncryptPool(
            get_object(pool_object_path),
            {
                "key_descs": (
                    []
                    if namespace.key_desc is None
                    else [((False, 0), namespace.key_desc)]
                ),
                "clevis_infos": (
                    []
                    if namespace.clevis is None
                    else [
                        (
                            (False, 0),
                            namespace.clevis.pin,
                            json.dumps(namespace.clevis.config),
                        )
                    ]
                ),
            },
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        if not changed:  # pragma: no cover
            raise StratisCliIncoherenceError(
                f"Expected to change {pool_id} encryption status to "
                "encrypted, but stratisd reports that it did not change "
                "the encryption status"
            )

    @staticmethod
    @long_running_operation
    def unencrypt(namespace: Namespace):
        """
        Unencrypt a previously encrypted pool.
        """
        if not namespace.in_place:
            raise StratisCliInPlaceNotSpecified()

        # pylint: disable=import-outside-toplevel
        from ._data import MOPool, ObjectManager, pool_spec, pools

        Pool = _make_class(  # pylint: disable=invalid-name
            pool_spec, "Pool", methods=["DecryptPool"], timeout=10
        )

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

        if return_code != StratisdErrors.OK:  # pragma: no cover
            raise StratisCliEngineError(return_code, message)

        if not changed:  # pragma: no cover
            raise StratisCliIncoherenceError(
                f"Expected to change {pool_id} encryption status to "
                "unencrypted, but stratisd reports that it did not change "
                "the pool's encryption status"
            )

    @staticmethod
    @long_running_operation
    def reencrypt(namespace: Namespace):
        """
        Reencrypt an already encrypted pool with a new key.
        """
        if not namespace.in_place:
            raise StratisCliInPlaceNotSpecified()

        # pylint: disable=import-outside-toplevel
        from ._data import ObjectManager, pool_spec, pools

        Pool = _make_class(  # pylint: disable=invalid-name
            pool_spec, "Pool", methods=["ReencryptPool"], timeout=10
        )

        pool_id = PoolId.from_parser_namespace(namespace)
        assert pool_id is not None

        proxy = get_object(TOP_OBJECT)

        managed_objects = ObjectManager.Methods.GetManagedObjects(proxy, {})

        (pool_object_path, _) = next(
            pools(props=pool_id.managed_objects_key())
            .require_unique_match(True)
            .search(managed_objects)
        )

        (changed, return_code, message) = Pool.Methods.ReencryptPool(
            get_object(pool_object_path), {}
        )

        if return_code != StratisdErrors.OK:
            raise StratisCliEngineError(return_code, message)

        if not changed:  # pragma: no cover
            raise StratisCliIncoherenceError(
                f"Expected to reencrypt {pool_id} with a new key but stratisd "
                "reports that it did not perform the operation"
            )
