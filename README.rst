CLI for Stratis Project
=================================

A CLI for the Stratis Project.

Introduction
------------
The CLI for the Stratis Project is a Python shell which communicates with the
Stratis daemon, stratisd, via dbus.

As a matter of principle, it concerns itself solely with parsing arguments,
passing them to the dbus API, and displaying the results returned by stratisd
when appropriate. It is stateless and does not contain any storage-related
logic.

Installing
----------

To install, check out the source, and use the included setup script, as::

   > python setup.py install

Running
-------
After installing, running just requires invoking the script, as::

   > stratis --help

or::

   > stratis --version

To run without installing, check out the source, change to the top directory
and enter::

   > ./bin/stratis --help

making sure that your PYTHONPATH environment variable is set to the CLI src
directory.

If you are not running the Stratis sdbus service most actions will be
unavailable, but all help menus should work properly.

Testing
-------
There are some unit and integration tests in the tests directory.

These can be run by setting your PYTHONPATH environment variable to the CLI
src directory and entering::

   > py.test tests

at the command prompt. Entering::

   > tox

will cause some tests to be run in the tox virtual environment. Integration
tests, which requires the CLI to connect with the Stratis daemon, will not
be run.


General Principles
------------------
The CLI command-line is intended to have a simple structure to avoid
ambiguities and constraints in parsing. For that reason, the initial portion
of the command-line is a list of menu-selectors, each of which selects an
option from the menu belonging to the previous selector. Once the final
sub-menu is selected the remaining cli consists of options and arguments, only.

Architecture
------------
The CLI consists of several orthogonal sub-packages.

The dbus package consists solely of Python wrappers for dbus interfaces.
Some interfaces are standard, like ObjectManager and Introspectable.
Other are specific to stratis.

The parser package consists solely of mechanisms for constructing parsers
using the Python argparse package.

The actions package contains code that mediates between the parser and the
dbus package. It contains functions that are automatically invoked by the
parser during execution. Each function takes a parser Namespace argument,
interprets it, and makes the necessary dbus calls.
