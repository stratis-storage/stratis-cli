"""
General constants for testing.
"""
import pyudev

_STRATISD = '/home/mulhern/my-contributions/stratisd'
_STRATISD_EXECUTABLE = 'stratisd'

_DEVICES = \
   [x for x in pyudev.Context().list_devices(subsystem='block', DEVTYPE='disk')]
