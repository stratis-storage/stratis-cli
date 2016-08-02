from os import path

import pyudev

from ._errors import StratisCliValueError

_CONTEXT = pyudev.Context()


def device_from_path(device_path):
    """
    Return the device node path corresponding to the path.

    :param str device_path: a string representing a path to a device
    :returns: the device node corresponding to the path
    :rtype: str
    :raises: StratisCliValueError
    """
    if path.islink(device_path):
        if path.exists(device_path):
            device_node = path.realpath(device_path)
        else:
            raise StratisCliValueError(
                device_path,
                "device_path",
                "is a bad link"
            )
    else:
        device_node = device_path

    try:
        pyudev.Devices.from_device_file(_CONTEXT, device_node)
    except pyudev.DeviceNotFoundError as err:
        raise StratisCliValueError(
            device_path,
            "device_path",
            "device node not found: %s" % err
        )

    return device_node
