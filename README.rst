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
You can install ``stratis-cli`` directly from the ``stratis-cli`` project
repo.

``stratis-cli`` has a number of dependencies that may not already be
installed. You may choose to allow the setup script to install any missing
dependencies from PyPi, or you may prefer to install the dependencies using
your distribution's package manager. All ``stratis-cli``'s direct
dependencies are listed in ``stratis-cli``'s setup.py file, in the
``install_requires`` field. If you choose to install the dependencies
using your installation's package manager, you should do so before you
run the setup.py script.

Finally, run the setup.py script as::

   > python setup.py install

Running
-------
After installing, running requires invoking the script, as::

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
Various testing modalities are used to verify various properties of
``stratis``.  Please consult the README files in the ``tests`` subdirectory
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

Tab Completion
--------------
From time to time, our external contributors have added support for
tab-completion in a variety of different shells. The files are included in the
stratis-cli GitHub release, but they are not supported by the Stratis project.
We welcome further contributions to these files and will continue to include
them for as long as they seem useful to our users.
