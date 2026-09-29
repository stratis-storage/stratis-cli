CLI for Stratis Project
=================================

A CLI for the Stratis Project.

Introduction
------------
`stratis-cli` is a tool that provides a command-line interface (CLI)
for interacting with the Stratis daemon,
`stratisd <https://github.com/stratis-storage/stratisd>`_. ``stratis-cli``
interacts with ``stratisd`` via
`D-Bus <https://www.freedesktop.org/wiki/Software/dbus/>`_. It is
written in Python 3.

``stratis-cli`` is stateless and contains a minimum of storage-related
logic. Its code mainly consists of parsing arguments from the command
line, calling methods that are part of the Stratis D-Bus API, and then
processing and displaying the results.

Installing
----------
You can install ``stratis-cli`` using your distribution's package manager.

You can install ``stratis-cli`` from PyPI or from the ``stratis-cli``
project repo using ``pip``.

``stratis-cli`` in-development releases are available for Fedora via Copr at
the ``packit/stratis-storage-stratis-cli-master-copr_commit`` Copr repo.

Running
-------
Running requires invoking the ``stratis`` command, as::

   > stratis --help

or::

   > stratis --version

Most ``stratis`` commands will fail unless you are also running the
`Stratis daemon <https://github.com/stratis-storage/stratisd>`_ and have
root permissions.

Testing
-------
Various testing modalities are used to verify various properties of
``stratis``.  Please consult the README file in the ``tests`` subdirectory
for further information.

The project has, and will continue to maintain, 100% code coverage.

Internal Software Architecture
------------------------------
``stratis`` is implemented in two parts:

* The *parser* package handles configuring the command line parser, which uses
  the Python `argparse <https://docs.python.org/3/library/argparse.html>`_ package.

* The *actions* package receives valid commands from the parser package
  and executes them, invoking the D-Bus API as needed.  The parser
  passes command-line arguments given by the user to methods in the
  actions package using a ``Namespace`` object.

Python Coding Style
-------------------
``stratis`` conforms to PEP-8 style guidelines as enforced by the ``black``
formatting tool.
