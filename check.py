#!/usr/bin/python3

"""
Invoke pylint with pre-selected-options.
"""

# isort: STDLIB
import argparse
import subprocess
import sys

ARG_MAP = {
    "check.py": [
        "--reports=no",
        "--disable=I",
        "--msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
    ],
    "setup.py": [
        "--reports=no",
        "--disable=I",
        "--msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
    ],
    "src/stratis_cli": [
        "--reports=no",
        "--disable=I",
        "--disable=duplicate-code",
        "--msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
    ],
    "tests/blackbox/stratisd_cert.py": [
        "--reports=no",
        "--disable=I",
        "--msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
    ],
    "tests/blackbox/stratis_cli_cert.py": [
        "--reports=no",
        "--disable=I",
        "--msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
    ],
    "tests/blackbox/testlib": [
        "--reports=no",
        "--disable=I",
        "--msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
    ],
    "tests/whitebox": [
        "--reports=no",
        "--disable=I",
        "--disable=duplicate-code",
        "--msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
    ],
    "bin/stratis": [
        "--reports=no",
        "--msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
    ],
}


def get_parser():
    """
    Generate an appropriate parser.

    :returns: an argument parser
    :rtype: `ArgumentParser`
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "package", choices=ARG_MAP.keys(), help="designates the package to test"
    )
    return parser


def get_command(namespace):
    """
    Get the pylint command for these arguments.

    :param `Namespace` namespace: the namespace
    """
    return ["pylint", namespace.package] + ARG_MAP[namespace.package]


def main():
    """
    Run the linter on a single directory or file.
    """
    args = get_parser().parse_args()
    return subprocess.call(get_command(args), stdout=sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
