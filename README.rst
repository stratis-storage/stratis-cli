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
stratisd-client-dbus, into-dbus-python, dbus-signature-pyparsing.

Finally, ensure you have python3-pyparsing package installed.

Troubleshooting
---------------
Error::

> Traceback (most recent call last):
>   File "/usr/bin/stratis", line 4, in <module>
>     __import__('pkg_resources').run_script('stratis-cli==0.0.2', 'stratis')
>   File "/usr/lib/python3.6/site-packages/pkg_resources/__init__.py", line 739, in run_script
>     self.require(requires)[0].run_script(script_name, ns)
>   File "/usr/lib/python3.6/site-packages/pkg_resources/__init__.py", line 1501, in run_script
>     exec(script_code, namespace, namespace)
>   File "/usr/lib/python3.6/site-packages/stratis_cli-0.0.2-py3.6.egg/EGG-INFO/scripts/stratis", line 23, in <module>
>   File "/usr/lib/python3.6/site-packages/stratis_cli-0.0.2-py3.6.egg/stratis_cli/__init__.py", line 19, in <module>
>   File "/usr/lib/python3.6/site-packages/stratis_cli-0.0.2-py3.6.egg/stratis_cli/_main.py", line 20, in <module>
> ModuleNotFoundError: No module named 'dbus'


Solution: Install python3.4 and python34-dbus

Running
-------
After installing, running just requires invoking the script, as::

   > stratis --help

or::

   > stratis --version

To run without installing, check out the source, change to the top
directory and set the ``PYTHONPATH`` environment variable to include
library dependencies. For example (if using bash shell)::

   > export PYTHONPATH="src:../stratisd-client-dbus/src:../into-dbus-python/src:../dbus-signature-pyparsing/src"
   > ./bin/stratis --help

Since ``stratis`` uses stratisd's API, most operations will fail
unless you are also running the `Stratis daemon <https://github.com/stratis-storage/stratisd>`_.

Testing
-------
There are unit and integration tests in the ``tests`` directory.

Running tests depends on some additional packages: python3-pytest,
python3-hypothesis.

These can be run by setting the PYTHONPATH environment variable as
shown above, and also setting the STRATIS environment variable to the
absolute or relative path to your stratisd executable. For example
(again using bash shell)::

  > STRATISD=../stratisd/target/debug/stratisd make dbus-tests

*Note:* Since the tests invoke ``stratisd``, it should not be running
independently when the tests are run.

To run ``tox``, ensure python3-tox and dbus-glib-devel packages are
installed, and then run::

  > tox

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
``stratis`` uses PEP-8 style, with the additional rule that continuation lines
are indented 3 spaces.
