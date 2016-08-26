"""
Test 'destroy'.
"""

import unittest

from stratis_cli._main import run
from stratis_cli._errors import StratisCliRuntimeError
from stratis_cli._stratisd_constants import StratisdErrorsGen

from .._constants import _DEVICES

from .._misc import _device_list
from .._misc import Service


class DestroyTestCase(unittest.TestCase):
    """
    Test destroying a volume when the pool does not exist. In this case,
    an error should be raised, as the request is non-sensical.
    """
    _MENU = ['logical', 'destroy']
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

    def testDestroy(self):
        """
        Destruction of the volume must fail since pool is not specified.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        with self.assertRaises(StratisCliRuntimeError) as cm:
            all(run(command_line))
        expected_error = StratisdErrorsGen.get_object().STRATIS_POOL_NOTFOUND
        self.assertEqual(cm.exception.rc, expected_error)


class Destroy2TestCase(unittest.TestCase):
    """
    Test destroying a volume when the pool does exist but the volume does not.
    In this case, no error should be raised.
    """
    _MENU = ['logical', 'destroy']
    _POOLNAME = 'deadpool'
    _VOLNAMES = ['oubliette', 'mnemosyne']

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = \
           ['create', self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testDestroy(self):
        """
        Destruction of the volume must succeed since pool exists and at end
        volume is gone.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        all(run(command_line))

    def testForce(self):
        """
        Destruction of the volume must succeed since pool exists and at end
        volume is gone.
        """
        command_line = \
           self._MENU + [self._POOLNAME] + self._VOLNAMES + ['--force', '1']
        all(run(command_line))


class Destroy3TestCase(unittest.TestCase):
    """
    Test destroying a volume when the pool does exist and the volume does as
    well. In this case, the volumes should all be destroyed, and no error
    raised as there is no data on the volumes.
    """
    _MENU = ['logical', 'destroy']
    _POOLNAME = 'deadpool'
    _VOLNAMES = ['oubliette', 'mnemosyne']

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        self._service = Service()
        self._service.setUp()
        command_line = \
           ['create', self._POOLNAME] + \
           [d.device_node for d in _device_list(_DEVICES, 1)]
        all(run(command_line))

        command_line = ['logical', 'create', self._POOLNAME] + self._VOLNAMES
        all(run(command_line))

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._service.tearDown()

    def testDestroy(self):
        """
        Destruction of the volume must succeed since pool exists and at end
        volume is gone.
        """
        command_line = self._MENU + [self._POOLNAME] + self._VOLNAMES
        all(run(command_line))

    def testForce(self):
        """
        Destruction of the volume must succeed since pool exists and at end
        volume is gone.
        """
        command_line = \
           self._MENU + [self._POOLNAME] + self._VOLNAMES + ['--force', '1']
        all(run(command_line))
