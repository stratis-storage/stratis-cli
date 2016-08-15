"""
Miscellaneous methods to support testing.
"""

import random

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
