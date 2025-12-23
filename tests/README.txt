This directory contains tests of the CLI functionality.

There are three directories containing three types of tests:
* unit - strict unit tests which require no setup of the environment
* integration - straightforward tests of functionality

The project Makefile has make targets for running these different categories
of tests.

As is usual with Python projects, it is essential to set the PYTHONPATH
environment variable correctly when running the tests.

With the exception of the tests in the unit directory, all tests
require a stratisd executable. To run the tests, it is necessary to
set the value of the environment variable STRATISD to the path of the
stratisd executable. The tests start and stop stratisd regularly; the
results will be incorrect if stratisd is already running when the tests
are begun. All these tests are run against the simulator engine; they will
not cause any operations on any real block devices.
