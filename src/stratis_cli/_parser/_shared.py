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
Shared parser operations.
"""

# isort: STDLIB
import argparse
import copy
import re
from uuid import UUID

# isort: THIRDPARTY
from justbytes import B, GiB, KiB, MiB, PiB, Range, TiB

from .._constants import Clevis
from .._stratisd_constants import ClevisInfo

CLEVIS_KEY_TANG_TRUST_URL = "stratis:tang:trust_url"
CLEVIS_PIN_TANG = "tang"
CLEVIS_PIN_TPM2 = "tpm2"
CLEVIS_KEY_THP = "thp"
CLEVIS_KEY_URL = "url"

_RANGE_RE = re.compile(r"^(?P<magnitude>[0-9]+)(?P<units>([KMGTP]i)?B)$")

_SIZE_SPECIFICATION = (
    "Size must be specified using the format <magnitude><units> where "
    "<magnitude> is a decimal integer value and <units> is any binary "
    'unit specifier in the set "B", "KiB", "MiB", "GiB", "TiB", '
    'and "PiB".'
)


def _unit_map(unit_specifier):
    """
    A simple function that maps a unit_specifier string
    call to a justbytes unit designation.

    :param str unit_specifier: the string
    :returns: the corresponding justbytes units
    :rtype: justbytes.BinaryUnit
    """
    if unit_specifier == "B":
        return B
    if unit_specifier == "KiB":
        return KiB
    if unit_specifier == "MiB":
        return MiB
    if unit_specifier == "GiB":
        return GiB
    if unit_specifier == "TiB":
        return TiB
    if unit_specifier == "PiB":
        return PiB
    assert False, f'Unknown unit specifier "{unit_specifier}"'


def parse_range(values):
    """
    Parse a range value.

    :param str values: string to parse
    """
    match = _RANGE_RE.search(values)
    if match is None:
        raise argparse.ArgumentTypeError(
            f"Ill-formed size specification: {_SIZE_SPECIFICATION}"
        )

    (magnitude, unit) = (match.group("magnitude"), match.group("units"))

    units = _unit_map(unit)

    result = Range(int(magnitude), units)

    assert result.magnitude.denominator == 1

    return result


class RejectAction(argparse.Action):
    """
    Just reject any use of the option.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        raise argparse.ArgumentError(
            self, f"Option {option_string} can not be assigned to or set."
        )


class DefaultAction(argparse.Action):
    """
    Detect if the default value was set.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, self.dest + "_default", False)


def ensure_nat(arg):
    """
    Raise error if argument is not an natural number.
    """
    try:
        result = int(arg)
    except Exception as err:
        raise argparse.ArgumentTypeError(
            f"Argument {arg} is not a natural number."
        ) from err

    if result < 0:
        raise argparse.ArgumentTypeError(f"Argument {arg} is not a natural number.")
    return result


class MoveNotice:  # pylint: disable=too-few-public-methods
    """
    Constructs a move notice, for printing.
    """

    def __init__(self, name, deprecated, preferred, version_completed):
        """
        Initializer.

        :param str name: the name of the moved command
        :param str deprecated: the deprecated command-line prefix
        :param str preferred: the preferred command-line prefix
        :param str version_completed: the version of stratis move is completed
        """
        self.name = name
        self.deprecated = deprecated
        self.preferred = preferred
        self.version_completed = version_completed

    def __str__(self):
        return (
            f'MOVE NOTICE: The "{self.name}" subcommand can also be found '
            f'under the "{self.preferred}" subcommand. The '
            f'"{self.deprecated} {self.name}" subcommand that you are using '
            "now is deprecated and will be removed in stratis "
            f"{self.version_completed}."
        )


UUID_OR_NAME = [
    (
        "--name",
        {
            "help": "name",
        },
    ),
    (
        "--uuid",
        {
            "type": UUID,
            "help": "UUID",
        },
    ),
]

KEYFILE_PATH_OR_STDIN = [
    (
        "--keyfile-path",
        {"help": "Path to a key file containing a key"},
    ),
    (
        "--capture-key",
        {
            "action": "store_true",
            "help": (
                "Read key from stdin with no terminal echo or userspace "
                "buffer storage"
            ),
        },
    ),
]

TRUST_URL_OR_THUMBPRINT = [
    (
        "--trust-url",
        {
            "action": "store_true",
            "help": "Omit verification of tang server credentials",
        },
    ),
    (
        "--thumbprint",
        {
            "help": "Thumbprint of tang server at specified URL",
        },
    ),
]


class ClevisEncryptionOptions:  # pylint: disable=too-few-public-methods
    """
    Gathers and verifies encryption options.
    """

    def __init__(self, namespace):
        self.clevis = copy.copy(namespace.clevis)
        del namespace.clevis

        self.thumbprint = copy.copy(namespace.thumbprint)
        del namespace.thumbprint

        self.tang_url = copy.copy(namespace.tang_url)
        del namespace.tang_url

        self.trust_url = copy.copy(namespace.trust_url)
        del namespace.trust_url

    def verify(self, namespace, parser):
        """
        Do supplementary parsing of conditional arguments.
        """
        if self.clevis in (Clevis.NBDE, Clevis.TANG) and self.tang_url is None:
            parser.error(
                "Specified binding with Clevis Tang server, but URL was not "
                "specified. Use --tang-url option to specify tang URL."
            )

        if self.tang_url is not None and (
            not self.trust_url and self.thumbprint is None
        ):
            parser.error(
                "Specified binding with Clevis Tang server, but neither "
                "--thumbprint nor --trust-url option was specified."
            )

        if self.tang_url is not None and (
            self.clevis not in (Clevis.NBDE, Clevis.TANG)
        ):
            parser.error(
                "Specified --tang-url without specifying Clevis encryption "
                "method. Use --clevis=tang to choose Clevis encryption."
            )

        if (self.trust_url or self.thumbprint is not None) and self.tang_url is None:
            parser.error(
                "Specified --trust-url or --thumbprint without specifying tang "
                "URL. Use --tang-url to specify URL."
            )

        namespace.clevis = (
            None
            if self.clevis is None
            else (
                ClevisInfo(
                    CLEVIS_PIN_TANG,
                    {CLEVIS_KEY_URL: self.tang_url}
                    | (
                        {CLEVIS_KEY_TANG_TRUST_URL: True}
                        if self.trust_url
                        else {CLEVIS_KEY_THP: self.thumbprint}
                    ),
                )
                if self.clevis in (Clevis.NBDE, Clevis.TANG)
                else ClevisInfo(CLEVIS_PIN_TPM2, {})
            )
        )


CLEVIS_AND_KERNEL = [
    (
        "--key-desc",
        {
            "help": ("Key description of key in kernel keyring"),
        },
    ),
    (
        "--clevis",
        {
            "type": Clevis,
            "help": "Specification for binding with Clevis.",
            "choices": list(Clevis),
        },
    ),
    (
        "--tang-url",
        {
            "help": "URL of Clevis tang server (--clevis=[tang|nbde] must be set)",
        },
    ),
]

IN_PLACE = [
    (
        "--in-place",
        {
            "action": "store_true",
            "help": (
                "Perform the operation in place; requires no additional "
                "devices; this operation can not in general be rolled back on "
                "failure"
            ),
        },
    )
]
