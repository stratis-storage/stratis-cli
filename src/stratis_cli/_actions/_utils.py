# Copyright 2020 Red Hat, Inc.
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
Miscellaneous functions.
"""

# isort: STDLIB
import json

from .._errors import (
    StratisCliEnginePropertyError,
    StratisCliMissingClevisTangURLError,
    StratisCliMissingClevisThumbprintError,
    StratisCliPropertyNotFoundError,
)
from .._stratisd_constants import (
    CLEVIS_KEY_TANG_TRUST_URL,
    CLEVIS_KEY_THP,
    CLEVIS_KEY_URL,
    CLEVIS_PIN_TANG,
    CLEVIS_PIN_TPM2,
)


def unpack_property(props, name):
    """
    Get a property fetched through FetchProperties interface

    :param props: dictionary of property names mapped to values
    :type props: dict of strs to (bool, object)
    :param name: the name of the property
    :type name: str
    :returns: the object in the dict
    :raises StratisCliPropertyNotFoundError:
    :raises StratisCliEnginePropertyError:
    """
    # Disable coverage for failure of the engine to successfully get a value
    # or for a property not existing for a specified key. We can not force the
    # engine error easily and should not force it these CLI tests. A KeyError
    # can only be raised if there is a bug in the code or if the version of
    # stratisd being run is not compatible with the version of the CLI being
    # tested. We expect to avoid those conditions, and choose not to test for
    # them.
    try:
        (success, variant) = props[name]
        if not success:
            raise StratisCliEnginePropertyError(name, variant)  # pragma: no cover
        return variant
    except KeyError as err:  # pragma: no cover
        raise StratisCliPropertyNotFoundError(name) from err


def fetch_property(proxy, property_name):
    """
    Fetch a property from stratisd.
    :param proxy: proxy to the top object in stratisd
    :param str property_name: name of the property to fetch
    :return: value associated with the requested property name
    :raises StratisCliPropertyNotFoundError:
    :raises StratisCliEnginePropertyError:
    """
    # pylint: disable=import-outside-toplevel
    from ._data import FetchProperties

    properties = FetchProperties.Methods.GetProperties(
        proxy, {"properties": [property_name]}
    )
    return unpack_property(properties, property_name)


def get_clevis_info(namespace):
    """
    Get clevis info, if any, from the namespace.

    :param namespace: namespace set up by the parser

    :returns: clevis info or None
    :rtype: pair of str or NoneType
    """
    clevis_info = None
    if namespace.clevis is not None:
        if namespace.clevis in ("nbde", "tang"):
            if namespace.tang_url is None:
                raise StratisCliMissingClevisTangURLError()

            if not namespace.trust_url and namespace.thumbprint is None:
                raise StratisCliMissingClevisThumbprintError()

            clevis_config = {CLEVIS_KEY_URL: namespace.tang_url}
            if namespace.trust_url:
                clevis_config[CLEVIS_KEY_TANG_TRUST_URL] = True
            else:
                assert namespace.thumbprint is not None
                clevis_config[CLEVIS_KEY_THP] = namespace.thumbprint

            clevis_info = (CLEVIS_PIN_TANG, clevis_config)

        elif namespace.clevis == "tpm2":
            clevis_info = (CLEVIS_PIN_TPM2, {})

        else:
            raise AssertionError(
                "unexpected value %s for clevis option" % namespace.clevis
            )  # pragma: no cover

    return (
        clevis_info
        if clevis_info is None
        else (clevis_info[0], json.dumps(clevis_info[1]))
    )


def get_pool_object_path(top_object, name):
    """
    Get a pool's object path based on its name.

    :param top_object: the top object
    :param str name: the pool name
    """
    # pylint: disable=import-outside-toplevel
    from ._data import ObjectManager, pools

    managed_objects = ObjectManager.Methods.GetManagedObjects(top_object, {})
    (pool_object_path, _) = next(
        pools(props={"Name": name}).require_unique_match(True).search(managed_objects)
    )
    return pool_object_path
