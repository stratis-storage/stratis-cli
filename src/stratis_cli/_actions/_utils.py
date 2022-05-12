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
    StratisCliMissingClevisTangURLError,
    StratisCliMissingClevisThumbprintError,
)
from .._stratisd_constants import (
    CLEVIS_KEY_TANG_TRUST_URL,
    CLEVIS_KEY_THP,
    CLEVIS_KEY_URL,
    CLEVIS_PIN_TANG,
    CLEVIS_PIN_TPM2,
)


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
                "unexpected value {namespace.clevis} for clevis option"
            )  # pragma: no cover

    return (
        clevis_info
        if clevis_info is None
        else (clevis_info[0], json.dumps(clevis_info[1]))
    )
