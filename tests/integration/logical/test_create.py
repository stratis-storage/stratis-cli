"""
Test 'create'.
"""

import unittest

from cli._main import run
from cli._errors import StratisCliRuntimeError
from cli._stratisd_constants import StratisdErrorsGen

from .._constants import _DEVICES

from .._misc import _device_list
from .._misc import Service


class CreateTestCase(unittest.TestCase):
    """
    Test creating a volume w/out a pool.
    """
    _MENU = ['logical', 'create']
    _POOLNAME = 'deadpool'
    _VOLNAMES = ['oubliette', 'mnemosyne']

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testCreation(self):
        """
        Creation of the volume must fail since pool is not specified.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        with self.assertRaises(StratisCliRuntimeError) as cm:
            all(run(command_line))
        expected_error = StratisdErrorsGen.get_object().STRATIS_POOL_NOTFOUND
        self.assertEqual(cm.exception.rc, expected_error)


@unittest.skip("Creation of a volume could fail if no room in pool.")
class Create2TestCase(unittest.TestCase):
    """
    Test creating a volume w/ a pool.
    """
    _MENU = ['logical', 'create']
    _POOLNAME = 'deadpool'
    _VOLNAMES = ['oubliette', 'mnemosyne']

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = \
           ['create'] + [self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testCreation(self):
        """
        Creation of the volume should succeed since pool is available.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        all(run(command_line))
