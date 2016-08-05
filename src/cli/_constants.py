"""
General constants.
"""

import dbus


SERVICE = 'org.storage.stratis1'
TOP_OBJECT = '/org/storage/stratis1'
MANAGER_INTERFACE = 'org.storage.stratis1.Manager'

BUS = dbus.SessionBus()
