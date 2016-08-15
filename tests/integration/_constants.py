"""
General constants for testing.
"""
import pyudev

_STRATISD = '/home/mulhern/my-contributions/stratisd'
_STRATISD_EXECUTABLE = 'stratisd'
_CLI = '/home/mulhern/my-projects/cli/src/main.py'

_DEVICES = list(pyudev.Context().list_devices(subsystem='block'))
