# Copyright 2016 Red Hat, Inc.
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
Miscellaneous methods to support testing.
"""

import os
import random
import subprocess

from ._constants import _STRATISD
from ._constants import _STRATISD_EXECUTABLE

def _device_list(devices, minimum):
    """
    Get a randomly selected list of devices with at least ``minimum`` elements.

    :param devices: list of device objects
    :type devices: list of pyudev.Device
    :param int minimum: the minimum number of devices, must be at least 0
    """
    limit = random.choice(range(minimum, len(devices)))
    indices = random.sample(range(len(devices)), limit)
    return [devices[i] for i in indices]


class Service(object):
    """
    Handle starting and stopping the service.
    """

    def setUp(self):
        """
        Start the stratisd daemon with the simulator.
        """
        env = dict(os.environ)
        env['LD_LIBRARY_PATH'] = os.path.join(_STRATISD, 'lib')

        bin_path = os.path.join(_STRATISD, 'bin')

        self._stratisd = subprocess.Popen(
           os.path.join(bin_path, _STRATISD_EXECUTABLE),
           env=env
        )

    def tearDown(self):
        """
        Stop the stratisd simulator and daemon.
        """
        self._stratisd.terminate()
