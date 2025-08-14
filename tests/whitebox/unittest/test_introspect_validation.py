import unittest
import xml.etree.ElementTree as ET

# Import the SPECS constant from the module under test.
# This file lives next to this test, so standard import should work.
from tests.whitebox.unittest.test_introspect import SPECS  # type: ignore


def is_valid_dbus_signature(sig: str) -> bool:
    """
    Very lightweight validator for DBus type signatures.
    It checks that the signature contains only valid type characters and that compound types
    have balanced parentheses and valid struct/dict/array ordering.

    Reference (simplified):
      - Basic types: ybnqiuxtdsogvh (plus 'a' for array, 'v' variant)
      - Struct: ( ... )
      - Dict entry: a{key value} where key is a basic type except 'v' and 'a', value is any valid type
      - Object path: 'o', Signature: 'g'
    """
    allowed_basic = set("ybnqiuxtdsogvh")
    i = 0
    n = len(sig)

    def parse_type(idx: int) -> int:
        if idx >= n:
            return -1
        ch = sig[idx]
        if ch in allowed_basic:
            return idx + 1
        if ch == 'a':  # array
            # array of any complete type or dict entry
            nxt = idx + 1
            if nxt < n and sig[nxt] == '{':
                # dict entry: a{kv}
                # parse key
                nxt += 1
                if nxt >= n:
                    return -1
                # key must be basic type except 'v' and arrays/containers
                if sig[nxt] in allowed_basic - set('v'):
                    nxt += 1
                else:
                    return -1
                # parse value type
                nxt2 = parse_type(nxt)
                if nxt2 == -1:
                    return -1
                if nxt2 >= n or sig[nxt2] != '}':
                    return -1
                return nxt2 + 1
            else:
                # array of a regular type
                nxt2 = parse_type(nxt)
                return -1 if nxt2 == -1 else nxt2
        if ch == '(':
            # struct: parse consecutive types until ')'
            nxt = idx + 1
            while nxt < n and sig[nxt] != ')':
                nxt2 = parse_type(nxt)
                if nxt2 == -1:
                    return -1
                nxt = nxt2
            if nxt >= n or sig[nxt] != ')':
                return -1
            return nxt + 1
        # everything else invalid
        return -1

    while i < n:
        j = parse_type(i)
        if j == -1:
            return False
        i = j
    return True


def get_interface(xml_text: str) -> ET.Element:
    # xml.etree requires a single root; the snippet already contains a single <interface> root
    try:
        root = ET.fromstring(xml_text.strip())
    except ET.ParseError as e:
        raise AssertionError(f"Invalid XML: {e}\nXML:\n{xml_text}") from e
    if root.tag != "interface":
        raise AssertionError(f"Root tag should be 'interface', got '{root.tag}'")
    return root


def find_method(interface: ET.Element, name: str) -> ET.Element:
    for m in interface.findall("method"):
        if m.get("name") == name:
            return m
    raise AssertionError(f"Method '{name}' not found in interface '{interface.get('name')}'")


def find_property(interface: ET.Element, name: str) -> ET.Element:
    for p in interface.findall("property"):
        if p.get("name") == name:
            return p
    raise AssertionError(f"Property '{name}' not found in interface '{interface.get('name')}'")


def assert_arg(elem: ET.Element, name: str, type_sig: str, direction: str) -> None:
    # Find arg by name under given method element
    for a in elem.findall("arg"):
        if a.get("name") == name:
            assert a.get("type") == type_sig, f"Arg '{name}' type mismatch: {a.get('type')} != {type_sig}"
            assert a.get("direction") == direction, f"Arg '{name}' direction mismatch: {a.get('direction')} != {direction}"
            assert is_valid_dbus_signature(type_sig), f"Arg '{name}' has invalid DBus signature: {type_sig}"
            return
    raise AssertionError(f"Arg '{name}' not found under '{elem.tag}' '{elem.get('name')}'")


def assert_property(elem: ET.Element, name: str, type_sig: str, access: str) -> ET.Element:
    p = find_property(elem, name)
    assert p.get("type") == type_sig, f"Property '{name}' type mismatch: {p.get('type')} != {type_sig}"
    assert p.get("access") == access, f"Property '{name}' access mismatch: {p.get('access')} != {access}"
    assert is_valid_dbus_signature(type_sig), f"Property '{name}' has invalid DBus signature: {type_sig}"
    return p


class TestIntrospectionSpecs(unittest.TestCase):
    def test_object_manager_interface_and_method(self):
        xml = SPECS["org.freedesktop.DBus.ObjectManager"]
        iface = get_interface(xml)
        self.assertEqual(iface.get("name"), "org.freedesktop.DBus.ObjectManager")
        m = find_method(iface, "GetManagedObjects")
        # Single out arg with complex signature
        assert_arg(m, "objpath_interfaces_and_properties", "a{oa{sa{sv}}}", "out")

    def test_manager_r9_methods_and_properties(self):
        xml = SPECS["org.storage.stratis3.Manager.r9"]
        iface = get_interface(xml)
        self.assertEqual(iface.get("name"), "org.storage.stratis3.Manager.r9")

        # CreatePool arguments (spot-check several complex args)
        m = find_method(iface, "CreatePool")
        assert_arg(m, "name", "s", "in")
        assert_arg(m, "devices", "as", "in")
        assert_arg(m, "key_desc", "a((bu)s)", "in")
        assert_arg(m, "clevis_info", "a((bu)ss)", "in")
        assert_arg(m, "journal_size", "(bt)", "in")
        assert_arg(m, "tag_spec", "(bs)", "in")
        assert_arg(m, "allocate_superblock", "(bb)", "in")
        assert_arg(m, "result", "(b(oao))", "out")
        assert_arg(m, "return_code", "q", "out")
        assert_arg(m, "return_string", "s", "out")

        # Other methods existence and key args
        for method_name in ["DestroyPool", "EngineStateReport", "ListKeys", "RefreshState",
                            "SetKey", "StartPool", "StopPool", "UnsetKey"]:
            _ = find_method(iface, method_name)

        # StartPool and StopPool spot-checks
        m_start = find_method(iface, "StartPool")
        assert_arg(m_start, "id", "s", "in")
        assert_arg(m_start, "id_type", "s", "in")
        assert_arg(m_start, "unlock_method", "(b(bu))", "in")
        assert_arg(m_start, "key_fd", "(bh)", "in")
        assert_arg(m_start, "remove_cache", "b", "in")
        assert_arg(m_start, "result", "(b(oaoao))", "out")
        assert_arg(m_start, "return_code", "q", "out")
        assert_arg(m_start, "return_string", "s", "out")

        m_stop = find_method(iface, "StopPool")
        assert_arg(m_stop, "id", "s", "in")
        assert_arg(m_stop, "id_type", "s", "in")
        assert_arg(m_stop, "result", "(bs)", "out")

        # Properties
        assert_property(iface, "StoppedPools", "a{sa{sv}}", "read")
        # Annotation checks
        p_version = assert_property(iface, "Version", "s", "read")
        found = False
        for ann in p_version.findall("annotation"):
            if ann.get("name") == "org.freedesktop.DBus.Property.EmitsChangedSignal" and ann.get("value") == "const":
                found = True
                break
        self.assertTrue(found, "Version property should have EmitsChangedSignal=const annotation")

    def test_report_r9_get_report(self):
        xml = SPECS["org.storage.stratis3.Report.r9"]
        iface = get_interface(xml)
        self.assertEqual(iface.get("name"), "org.storage.stratis3.Report.r9")
        m = find_method(iface, "GetReport")
        assert_arg(m, "name", "s", "in")
        assert_arg(m, "result", "s", "out")
        assert_arg(m, "return_code", "q", "out")
        assert_arg(m, "return_string", "s", "out")

    def test_blockdev_r9_properties(self):
        xml = SPECS["org.storage.stratis3.blockdev.r9"]
        iface = get_interface(xml)
        self.assertEqual(iface.get("name"), "org.storage.stratis3.blockdev.r9")

        # Basic and struct properties
        assert_property(iface, "Devnode", "s", "read")
        p_hw = assert_property(iface, "HardwareInfo", "(bs)", "read")
        p_init = assert_property(iface, "InitializationTime", "t", "read")
        assert_property(iface, "NewPhysicalSize", "(bs)", "read")
        p_phys = assert_property(iface, "PhysicalPath", "s", "read")
        p_pool = assert_property(iface, "Pool", "o", "read")
        p_tier = assert_property(iface, "Tier", "q", "read")
        assert_property(iface, "TotalPhysicalSize", "s", "read")
        assert_property(iface, "UserInfo", "(bs)", "readwrite")
        p_uuid = assert_property(iface, "Uuid", "s", "read")

        # Annotation checks: const and false on relevant properties
        def has_annotation(prop: ET.Element, value: str) -> bool:
            return any(
                a.get("name") == "org.freedesktop.DBus.Property.EmitsChangedSignal" and a.get("value") == value
                for a in prop.findall("annotation")
            )

        self.assertTrue(has_annotation(p_hw, "const"))
        self.assertTrue(has_annotation(p_init, "const"))
        self.assertTrue(has_annotation(p_phys, "const"))
        self.assertTrue(has_annotation(p_pool, "const"))
        self.assertTrue(has_annotation(p_uuid, "const"))
        self.assertTrue(has_annotation(p_tier, "false"))

    def test_filesystem_r9_methods_and_properties(self):
        xml = SPECS["org.storage.stratis3.filesystem.r9"]
        iface = get_interface(xml)
        self.assertEqual(iface.get("name"), "org.storage.stratis3.filesystem.r9")

        # Method
        m = find_method(iface, "SetName")
        assert_arg(m, "name", "s", "in")
        assert_arg(m, "result", "(bs)", "out")
        assert_arg(m, "return_code", "q", "out")
        assert_arg(m, "return_string", "s", "out")

        # Properties
        p_created = assert_property(iface, "Created", "s", "read")
        p_devnode = assert_property(iface, "Devnode", "s", "read")
        assert_property(iface, "MergeScheduled", "b", "readwrite")
        assert_property(iface, "Name", "s", "read")
        assert_property(iface, "Origin", "(bs)", "read")
        p_pool = assert_property(iface, "Pool", "o", "read")
        assert_property(iface, "Size", "s", "read")
        assert_property(iface, "SizeLimit", "(bs)", "readwrite")
        assert_property(iface, "Used", "(bs)", "read")
        p_uuid = assert_property(iface, "Uuid", "s", "read")

        # Annotation checks
        def has_annotation(prop: ET.Element, value: str) -> bool:
            return any(
                a.get("name") == "org.freedesktop.DBus.Property.EmitsChangedSignal" and a.get("value") == value
                for a in prop.findall("annotation")
            )

        self.assertTrue(has_annotation(p_created, "const"))
        # Devnode invalidates (validate presence and value)
        self.assertTrue(
            any(a.get("name") == "org.freedesktop.DBus.Property.EmitsChangedSignal" and a.get("value") == "invalidates"
                for a in p_devnode.findall("annotation")),
            "Devnode should have EmitsChangedSignal=invalidates annotation",
        )
        self.assertTrue(has_annotation(p_pool, "const"))
        self.assertTrue(has_annotation(p_uuid, "const"))

    def test_pool_r9_methods_and_properties(self):
        xml = SPECS["org.storage.stratis3.pool.r9"]
        iface = get_interface(xml)
        self.assertEqual(iface.get("name"), "org.storage.stratis3.pool.r9")

        required_methods = [
            "AddCacheDevs", "AddDataDevs", "BindClevis", "BindKeyring", "CreateFilesystems",
            "DecryptPool", "DestroyFilesystems", "EncryptPool", "FilesystemMetadata",
            "GrowPhysicalDevice", "InitCache", "Metadata", "RebindClevis", "RebindKeyring",
            "ReencryptPool", "SetName", "SnapshotFilesystem", "UnbindClevis", "UnbindKeyring"
        ]
        for mname in required_methods:
            _ = find_method(iface, mname)

        # Spot-check several methods' args and signatures
        m_add_cache = find_method(iface, "AddCacheDevs")
        assert_arg(m_add_cache, "devices", "as", "in")
        assert_arg(m_add_cache, "results", "(bao)", "out")
        assert_arg(m_add_cache, "return_code", "q", "out")
        assert_arg(m_add_cache, "return_string", "s", "out")

        m_create_fs = find_method(iface, "CreateFilesystems")
        assert_arg(m_create_fs, "specs", "a(s(bs)(bs))", "in")
        assert_arg(m_create_fs, "results", "(ba(os))", "out")

        m_metadata = find_method(iface, "Metadata")
        assert_arg(m_metadata, "current", "b", "in")
        assert_arg(m_metadata, "results", "s", "out")

        m_fsmeta = find_method(iface, "FilesystemMetadata")
        assert_arg(m_fsmeta, "fs_name", "(bs)", "in")
        assert_arg(m_fsmeta, "current", "b", "in")
        assert_arg(m_fsmeta, "results", "s", "out")

        # Properties with annotations
        assert_property(iface, "AllocatedSize", "s", "read")
        assert_property(iface, "AvailableActions", "s", "read")
        assert_property(iface, "ClevisInfos", "v", "read")
        assert_property(iface, "Encrypted", "b", "read")
        assert_property(iface, "FreeTokenSlots", "(by)", "read")
        assert_property(iface, "FsLimit", "t", "readwrite")
        assert_property(iface, "HasCache", "b", "read")
        assert_property(iface, "KeyDescriptions", "v", "read")
        assert_property(iface, "LastReencryptedTimestamp", "(bs)", "read")
        p_meta_ver = assert_property(iface, "MetadataVersion", "t", "read")
        assert_property(iface, "Name", "s", "read")
        assert_property(iface, "NoAllocSpace", "b", "read")
        assert_property(iface, "Overprovisioning", "b", "readwrite")
        assert_property(iface, "TotalPhysicalSize", "s", "read")
        assert_property(iface, "TotalPhysicalUsed", "(bs)", "read")
        p_uuid = assert_property(iface, "Uuid", "s", "read")
        p_vk = assert_property(iface, "VolumeKeyLoaded", "v", "read")

        def has_annotation(prop: ET.Element, value: str) -> bool:
            return any(
                a.get("name") == "org.freedesktop.DBus.Property.EmitsChangedSignal" and a.get("value") == value
                for a in prop.findall("annotation")
            )

        self.assertTrue(has_annotation(p_meta_ver, "const"))
        self.assertTrue(has_annotation(p_uuid, "const"))
        self.assertTrue(has_annotation(p_vk, "false"))

    def test_unknown_interface_key_handled(self):
        # Validate behavior when accessing unknown key: ensure KeyError is raised
        with self.assertRaises(KeyError):
            _ = SPECS["org.storage.stratis3.nonexistent"]

    def test_all_signatures_parse(self):
        # Exhaustively scan every arg/property type across all interfaces
        for key, xml in SPECS.items():
            iface = get_interface(xml)
            # args
            for m in iface.findall("method"):
                for a in m.findall("arg"):
                    sig = a.get("type") or ""
                    self.assertTrue(is_valid_dbus_signature(sig), f"{key}.{m.get('name')} arg '{a.get('name')}' invalid sig: {sig}")
            # properties
            for p in iface.findall("property"):
                sig = p.get("type") or ""
                self.assertTrue(is_valid_dbus_signature(sig), f"{key} property '{p.get('name')}' invalid sig: {sig}")

    def test_xml_is_well_formed(self):
        # Sanity: all XML snippets should be well-formed and single interface root
        for key, xml in SPECS.items():
            iface = get_interface(xml)
            self.assertEqual(iface.tag, "interface")
            self.assertIsNotNone(iface.get("name"), f"Interface name missing for key {key}")


if __name__ == "__main__":
    unittest.main()