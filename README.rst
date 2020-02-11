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

To install, check out the source, and use the included setup script, as::

   > python setup.py install

You will also need to obtain the following related Stratis repos:
dbus-client-gen, dbus-python-client-gen, into-dbus-python,
dbus-signature-pyparsing.

Finally, ensure you have python3-pyparsing package installed.

Running
-------
After installing, running just requires invoking the script, as::

   > stratis --help

or::

   > stratis --version

To run without installing, check out the source, change to the top
directory and set the ``PYTHONPATH`` environment variable to include
library dependencies. For example (if using bash shell)::

   > export PYTHONPATH="src:../dbus-client-gen/src:../dbus-python-client-gen/src:../into-dbus-python/src:../dbus-signature-pyparsing/src"
   > ./bin/stratis --help

Since ``stratis`` uses stratisd's API, most operations will fail
unless you are also running the `Stratis daemon <https://github.com/stratis-storage/stratisd>`_.

Testing
-------
There are unit and integration tests in the ``tests`` directory.

python3-pytest is required in order to run the tests.

These can be run by setting the PYTHONPATH environment variable as
shown above, and also setting the STRATIS environment variable to the
absolute or relative path to your stratisd executable. For example
(again using bash shell)::

  > STRATISD=../stratisd/target/debug/stratisd make dbus-tests

*Note:* Since the tests invoke ``stratisd``, it should not be running
independently when the tests are run.

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
