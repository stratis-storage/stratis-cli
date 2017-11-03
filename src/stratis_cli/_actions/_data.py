# Copyright 2017 Red Hat, Inc.
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
XML interface specifications.
"""

import xml.etree.ElementTree as ET

from dbus_client_gen import managed_object_class
from dbus_client_gen import mo_query_builder

from dbus_python_client_gen import make_class

from .._errors import StratisCliDbusLookupError


SPECS = {
"org.freedesktop.DBus.ObjectManager" :
"""
<interface name="org.freedesktop.DBus.ObjectManager">
<method name="GetManagedObjects">
<arg name="objpath_interfaces_and_properties" type="a{oa{sa{sv}}}" direction="out"/>
</method>
</interface>
""",
"org.storage.stratis1.Manager" :
"""
<interface name="org.storage.stratis1.Manager">
<method name="ConfigureSimulator">
<arg name="denominator" type="u" direction="in"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<method name="CreatePool">
<arg name="name" type="s" direction="in"/>
<arg name="redundancy" type="(bq)" direction="in"/>
<arg name="force" type="b" direction="in"/>
<arg name="devices" type="as" direction="in"/>
<arg name="result" type="(oas)" direction="out"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<method name="DestroyPool">
<arg name="pool" type="o" direction="in"/>
<arg name="action" type="b" direction="out"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<property name="ErrorValues" type="a(sq)" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
<property name="RedundancyValues" type="a(sq)" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
<property name="Version" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
</interface>
""",
"org.storage.stratis1.pool" :
"""
<interface name="org.storage.stratis1.pool">
<method name="AddDevs">
<arg name="force" type="b" direction="in"/>
<arg name="devices" type="as" direction="in"/>
<arg name="results" type="as" direction="out"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<method name="CreateFilesystems">
<arg name="specs" type="as" direction="in"/>
<arg name="filesystems" type="a(os)" direction="out"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<method name="DestroyFilesystems">
<arg name="filesystems" type="ao" direction="in"/>
<arg name="results" type="as" direction="out"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<method name="SnapshotFilesystem">
<arg name="origin" type="o" direction="in"/>
<arg name="snapshot_name" type="s" direction="in"/>
<arg name="result" type="o" direction="out"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<method name="SetName">
<arg name="name" type="s" direction="in"/>
<arg name="action" type="b" direction="out"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<property name="Name" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
</property>
<property name="TotalPhysicalSize" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
</property>
<property name="TotalPhysicalUsed" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
</property>
<property name="Uuid" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
</interface>
""",
"org.storage.stratis1.filesystem" :
"""
<interface name="org.storage.stratis1.filesystem">
<method name="SetName">
<arg name="name" type="s" direction="in"/>
<arg name="action" type="b" direction="out"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<property name="Devnode" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
<property name="Name" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
</property>
<property name="Pool" type="o" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
<property name="Uuid" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
</interface>
""",
"org.storage.stratis1.blockdev" :
"""
<interface name="org.storage.stratis1.blockdev">
<method name="SetUserInfo">
<arg name="id" type="s" direction="in"/>
<arg name="changed" type="b" direction="out"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<property name="Devnode" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
<property name="HardwareInfo" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
<property name="InitializationTime" type="t" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
<property name="Pool" type="o" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
<property name="State" type="q" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
</property>
<property name="TotalPhysicalSize" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
</property>
<property name="UserInfo" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
</property>
<property name="Uuid" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const"/>
</property>
</interface>
""",
}

Filesystem = make_class(
   "Filesystem",
   ET.fromstring(SPECS['org.storage.stratis1.filesystem'])
)
Manager = make_class(
   "Manager",
   ET.fromstring(SPECS['org.storage.stratis1.Manager'])
)
ObjectManager = make_class(
   "ObjectManager",
   ET.fromstring(SPECS['org.freedesktop.DBus.ObjectManager'])
)
Pool = make_class(
   "Pool",
   ET.fromstring(SPECS['org.storage.stratis1.pool'])
)

MOFilesystem = managed_object_class(
   "MOFilesystem",
   ET.fromstring(SPECS['org.storage.stratis1.filesystem'])
)
MOPool = managed_object_class(
   "MOPool",
   ET.fromstring(SPECS['org.storage.stratis1.pool'])
)
MODev = managed_object_class(
   "MODev",
   ET.fromstring(SPECS['org.storage.stratis1.blockdev'])
)

def _unique_wrapper(interface, func):
    """
    Wraps other methods, implementing an additional unique parameter.
    """
    def the_func(managed_objects, props=None, unique=False):
        """
        Call func on managed_objects and props. If unique is True, return
        the unique result or else raise an error. Otherwise, return the
        original result.

        :param dict managed_objects: result of calling GetManagedObjects()
        :param dict props: props to narrow search on, empty if None
        :param bool unique: whether the result is required to be unique

        :returns: the result of calling the_func, or a unique element
        :rtype: generator of str * dict OR a single pair of str * dict
        :raises StratisCliDbusLookupError: if unique == True and none found
        """
        result = func(managed_objects, props=props)
        if unique is True:
            result = [x for x in result]
            if len(result) != 1:
                raise StratisCliDbusLookupError(interface, props)
            return result[0]
        return result

    return the_func

_FILESYSTEM_INTERFACE = 'org.storage.stratis1.filesystem'
_filesystems = mo_query_builder(ET.fromstring(SPECS[_FILESYSTEM_INTERFACE]))
filesystems = _unique_wrapper(_FILESYSTEM_INTERFACE, _filesystems)

_POOL_INTERFACE = 'org.storage.stratis1.pool'
_pools = mo_query_builder(ET.fromstring(SPECS[_POOL_INTERFACE]))
pools = _unique_wrapper(_POOL_INTERFACE, _pools)

_BLOCKDEV_INTERFACE = 'org.storage.stratis1.blockdev'
_devs = mo_query_builder(ET.fromstring(SPECS[_BLOCKDEV_INTERFACE]))
devs = _unique_wrapper(_BLOCKDEV_INTERFACE, _devs)
