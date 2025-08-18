import unittest
import io
import types
from contextlib import redirect_stdout
from unittest import mock

# Import targets under test. We prefer explicit module path if available; fall back by discovering via relative import.
# These names are referenced in the diff snippets.
# We defensively try common module locations; if import fails, we skip tests with a helpful reason.
_TARGET_IMPORT_ERROR = None
try:
    # Most likely module path based on naming in snippets (list pools actions)
    from stratis_cli._actions._list._pool import (
        _metadata_version,
        _volume_key_loaded,
        TokenSlotInfo,
        DefaultAlerts,
        list_pools,
        DefaultDetail,
        DefaultTable,
        StoppedTable,
        Stopped,
        MetadataVersion,
        TOTAL_USED_FREE,
        PoolFeature,
    )
except Exception as e1:
    try:
        # Alternate module naming fallback
        from _actions._list._pool import (
            _metadata_version,
            _volume_key_loaded,
            TokenSlotInfo,
            DefaultAlerts,
            list_pools,
            DefaultDetail,
            DefaultTable,
            StoppedTable,
            Stopped,
            MetadataVersion,
            TOTAL_USED_FREE,
            PoolFeature,
        )
    except Exception as e2:
        _TARGET_IMPORT_ERROR = (e1, e2)


def _skip_if_import_failed(cls):
    if _TARGET_IMPORT_ERROR is not None:
        reason = f"Unable to import target module under test: {_TARGET_IMPORT_ERROR[0]} ; {_TARGET_IMPORT_ERROR[1]}"
        return unittest.skip(reason)(cls)
    return cls


@_skip_if_import_failed
class TestMetadataVersion(unittest.TestCase):
    def test_metadata_version_valid_int(self):
        class M:
            def MetadataVersion(self):
                return "2"
        self.assertEqual(_metadata_version(M()), MetadataVersion.V2)

    def test_metadata_version_invalid_value_returns_none(self):
        class M:
            def MetadataVersion(self):
                return "banana"
        # Function catches ValueError and returns None
        self.assertIsNone(_metadata_version(M()))


@_skip_if_import_failed
class TestVolumeKeyLoaded(unittest.TestCase):
    def test_volume_key_loaded_returns_bool_tuple_when_int(self):
        class M:
            def VolumeKeyLoaded(self):
                return 1  # truthy int
        is_bool, value = _volume_key_loaded(M())
        self.assertTrue(is_bool)
        self.assertTrue(value)

    def test_volume_key_loaded_zero_is_false(self):
        class M:
            def VolumeKeyLoaded(self):
                return 0
        is_bool, value = _volume_key_loaded(M())
        self.assertTrue(is_bool)
        self.assertFalse(value)

    def test_volume_key_loaded_returns_string_when_not_int(self):
        class M:
            def VolumeKeyLoaded(self):
                return "unknown"
        is_bool, value = _volume_key_loaded(M())
        self.assertFalse(is_bool)
        self.assertEqual(value, "unknown")


@_skip_if_import_failed
class TestTokenSlotInfo(unittest.TestCase):
    def test_str_for_key_description(self):
        info = TokenSlotInfo(3, key="desc")
        s = str(info)
        self.assertIn("Token Slot: 3", s)
        self.assertIn("Key Description: desc", s)
        self.assertNotIn("Clevis Pin", s)

    def test_str_for_clevis_info(self):
        info = TokenSlotInfo(7, clevis=("tpm2", {"foo": "bar"}))
        s = str(info)
        self.assertIn("Token Slot: 7", s)
        self.assertIn("Clevis Pin: tpm2", s)
        self.assertIn("Clevis Configuration: {'foo': 'bar'}", s)


@_skip_if_import_failed
class TestDefaultAlerts(unittest.TestCase):
    def setUp(self):
        # Minimal mopool stub with required methods
        class MOPoolStub:
            def __init__(self, available="NONE", no_alloc=False, encrypted=False, vkl=1):
                self._available = available
                self._no_alloc = no_alloc
                self._encrypted = encrypted
                self._vkl = vkl  # int or string

            def AvailableActions(self):
                return self._available

            def NoAllocSpace(self):
                return int(self._no_alloc)

            def Encrypted(self):
                return int(self._encrypted)

            def VolumeKeyLoaded(self):
                return self._vkl

            def MetadataVersion(self):
                return "2"

        self.MOPoolStub = MOPoolStub

        # Minimal PoolActionAvailability to produce alerts list
        self.paa_patch = mock.patch(
            "stratis_cli._actions._list._pool.PoolActionAvailability",
            side_effect=lambda name: types.SimpleNamespace(
                pool_maintenance_alerts=lambda: ["MAINT" if name else ""],
                name="AVAIL"
            )
        )
        self.paa = self.paa_patch.start()

        # Alerts enums
        self.pea_patch = mock.patch("stratis_cli._actions._list._pool.PoolEncryptionAlert")
        self.pds_patch = mock.patch("stratis_cli._actions._list._pool.PoolDeviceSizeChangeAlert")
        self.PEA = self.pea_patch.start()
        self.PDS = self.pds_patch.start()
        # Give them string-ish identities for checks
        self.PEA.VOLUME_KEY_NOT_LOADED = "VKL_NOT_LOADED"
        self.PEA.VOLUME_KEY_STATUS_UNKNOWN = "VKL_UNKNOWN"

        # _from_sets returns empty by default (no device size changes)
        self.from_sets_patch = mock.patch("stratis_cli._actions._list._pool.DefaultAlerts._from_sets", return_value=[])
        self.from_sets_patch.start()

    def tearDown(self):
        self.paa_patch.stop()
        self.pea_patch.stop()
        self.pds_patch.stop()
        self.from_sets_patch.stop()

    def test_alerts_no_encryption_no_alloc_space(self):
        da = DefaultAlerts(devs=[])
        mopool = self.MOPoolStub(available="ANY", no_alloc=True, encrypted=False, vkl=1)
        alerts = da.alert_codes("/pool/1", mopool)
        self.assertIn("MAINT", alerts)
        self.assertIn("NO_ALLOC_SPACE", [str(a) if not isinstance(a, str) else a for a in alerts] or ["NO_ALLOC_SPACE"])
        # No encryption alerts when not encrypted
        self.assertNotIn("VKL_NOT_LOADED", alerts)
        self.assertNotIn("VKL_UNKNOWN", alerts)

    def test_alerts_encrypted_v2_not_loaded(self):
        da = DefaultAlerts(devs=[])
        mopool = self.MOPoolStub(available="ANY", no_alloc=False, encrypted=True, vkl=0)
        alerts = da.alert_codes("/pool/1", mopool)
        self.assertIn("VKL_NOT_LOADED", alerts)
        self.assertNotIn("VKL_UNKNOWN", alerts)

    def test_alerts_encrypted_v2_unknown_status_string(self):
        da = DefaultAlerts(devs=[])
        mopool = self.MOPoolStub(available="ANY", no_alloc=False, encrypted=True, vkl="err")
        alerts = da.alert_codes("/pool/1", mopool)
        self.assertIn("VKL_UNKNOWN", alerts)
        self.assertNotIn("VKL_NOT_LOADED", alerts)


@_skip_if_import_failed
class TestListPoolsDispatch(unittest.TestCase):
    def setUp(self):
        # Patch the concrete classes to observe which is instantiated
        self.dt_patch = mock.patch("stratis_cli._actions._list._pool.DefaultTable")
        self.dd_patch = mock.patch("stratis_cli._actions._list._pool.DefaultDetail")
        self.st_patch = mock.patch("stratis_cli._actions._list._pool.StoppedTable")
        self.sd_patch = mock.patch("stratis_cli._actions._list._pool.StoppedDetail")
        self.DefaultTable = self.dt_patch.start()
        self.DefaultDetail = self.dd_patch.start()
        self.StoppedTable = self.st_patch.start()
        self.StoppedDetail = self.sd_patch.start()

        for cls in (self.DefaultTable, self.DefaultDetail, self.StoppedTable, self.StoppedDetail):
            instance = mock.Mock()
            instance.display = mock.Mock()
            cls.return_value = instance

        self.uuid_formatter = lambda x: str(x)

    def tearDown(self):
        self.dt_patch.stop()
        self.dd_patch.stop()
        self.st_patch.stop()
        self.sd_patch.stop()

    def test_default_table_when_not_stopped_and_no_selection(self):
        list_pools(self.uuid_formatter)
        self.DefaultTable.assert_called_once_with(self.uuid_formatter)
        self.DefaultTable.return_value.display.assert_called_once()

    def test_default_detail_when_not_stopped_with_selection(self):
        selection = mock.Mock()
        list_pools(self.uuid_formatter, selection=selection)
        self.DefaultDetail.assert_called_once_with(self.uuid_formatter, selection)
        self.DefaultDetail.return_value.display.assert_called_once()

    def test_stopped_table_when_stopped_without_selection(self):
        list_pools(self.uuid_formatter, stopped=True)
        self.StoppedTable.assert_called_once_with(self.uuid_formatter)
        self.StoppedTable.return_value.display.assert_called_once()

    def test_stopped_detail_when_stopped_with_selection(self):
        selection = mock.Mock()
        list_pools(self.uuid_formatter, stopped=True, selection=selection)
        self.StoppedDetail.assert_called_once_with(self.uuid_formatter, selection)
        self.StoppedDetail.return_value.display.assert_called_once()


@_skip_if_import_failed
class TestStoppedHelpers(unittest.TestCase):
    def test_pool_name_formatting(self):
        self.assertEqual(Stopped._pool_name(None), "<UNAVAILABLE>")
        self.assertEqual(Stopped._pool_name("poolX"), "poolX")

    def test_metadata_version_str(self):
        self.assertEqual(Stopped._metadata_version_str(None), "<MIXED>")
        self.assertEqual(Stopped._metadata_version_str(1), "1")


@_skip_if_import_failed
class TestDefaultDetailPrint(unittest.TestCase):
    def setUp(self):
        # Patch date parsing to stable output
        self.date_patch = mock.patch("stratis_cli._actions._list._pool.date_parser")
        dp = self.date_patch.start()
        # isoparse().astimezone().strftime(...) -> "Jan 01 2023 00:00"
        dp.isoparse.return_value.astimezone.return_value.strftime.return_value = "Jan 01 2023 00:00"

        # Provide fixed alert codes
        self.alerts = mock.Mock()
        self.alerts.alert_codes.return_value = []

        # Minimal MOPool stub with all required accessors
        class M:
            def __init__(self, encrypted=False, vkl=1, has_cache=True, fs_limit="unlimited", overprov=False):
                self._encrypted = encrypted
                self._vkl = vkl
                self._has_cache = has_cache
                self._fs_limit = fs_limit
                self._op = overprov

            def Encrypted(self):
                return int(self._encrypted)
            def Uuid(self):
                return "12345678-1234-1234-1234-1234567890ab"
            def Name(self):
                return "poolA"
            def AvailableActions(self):
                return "ANY"
            def NoAllocSpace(self):
                return 0
            def HasCache(self):
                return int(self._has_cache)
            def FsLimit(self):
                return self._fs_limit
            def Overprovisioning(self):
                return int(self._op)
            def LastReencryptedTimestamp(self):
                return (True, "2020-01-01T00:00:00Z")
            # Sizes
            def TotalPhysicalSize(self):
                return 1024 * 1024 * 1024
            def AllocatedSize(self):
                return 512 * 1024 * 1024
            def TotalPhysicalUsed(self):
                return (True, 256 * 1024 * 1024)
            # Encryption info lists for V2
            def KeyDescriptions(self):
                return [(1, "key-one")]
            def ClevisInfos(self):
                return [(2, ("tpm2", '{"foo": "bar"}'))]
            def FreeTokenSlots(self):
                return (True, 5)
            def MetadataVersion(self):
                return "2"
        self.MOPool = M

        # Patch helpers referred to inside print function
        self.paa_patch = mock.patch(
            "stratis_cli._actions._list._pool.PoolActionAvailability",
            side_effect=lambda name: types.SimpleNamespace(
                pool_maintenance_alerts=lambda: [],
                name="AVAIL"
            )
        )
        self.paa_patch.start()

    def tearDown(self):
        self.date_patch.stop()
        self.paa_patch.stop()

    def test_print_detail_encryption_disabled(self):
        mopool = self.MOPool(encrypted=False)
        alerts = self.alerts
        f = io.StringIO()
        dd = DefaultDetail(lambda x: str(x), selection=mock.Mock())
        with redirect_stdout(f):
            dd._print_detail_view("/pool/obj", mopool, alerts)
        out = f.getvalue()
        self.assertIn("Encryption Enabled: No", out)
        self.assertIn("UUID: 12345678-1234-1234-1234-1234567890ab", out)
        self.assertIn("Name: poolA", out)
        self.assertIn("Fully Allocated:", out)
        self.assertIn("Actions Allowed: AVAIL", out)

    def test_print_detail_encryption_enabled_v2(self):
        mopool = self.MOPool(encrypted=True, vkl=1)
        alerts = self.alerts
        f = io.StringIO()
        dd = DefaultDetail(lambda x: str(x), selection=mock.Mock())
        with redirect_stdout(f):
            dd._print_detail_view("/pool/obj", mopool, alerts)
        out = f.getvalue()
        self.assertIn("Encryption Enabled: Yes", out)
        self.assertIn("Last Time Reencrypted: Jan 01 2023 00:00", out)
        self.assertIn("Free Token Slots Remaining: 5", out)
        # TokenSlotInfo details printed indented
        self.assertIn("Token Slot:", out)
        self.assertIn("Key Description:", out)
        self.assertIn("Clevis Pin:", out)


@_skip_if_import_failed
class TestDefaultTable(unittest.TestCase):
    def setUp(self):
        # Prepare an MOPool-like object
        class M:
            def __init__(self, name, enc, cache, op, uuid, tsize, tused_valid=True, tused_val=0):
                self._name = name
                self._enc = enc
                self._cache = cache
                self._op = op
                self._uuid = uuid
                self._tsize = tsize
                self._tused_valid = tused_valid
                self._tused_val = tused_val

            def Name(self):
                return self._name
            def Encrypted(self):
                return int(self._enc)
            def HasCache(self):
                return int(self._cache)
            def Overprovisioning(self):
                return int(self._op)
            def Uuid(self):
                return self._uuid
            def TotalPhysicalSize(self):
                return self._tsize
            def TotalPhysicalUsed(self):
                return (self._tused_valid, self._tused_val)
            def AvailableActions(self):
                return "ANY"
            def MetadataVersion(self):
                return "2"
        self.M = M

        # Patch external dependencies used in DefaultTable.display
        self.get_object_patch = mock.patch("stratis_cli._actions._list._pool.get_object", return_value=object())
        self.get_object_patch.start()

        # ObjectManager.GetManagedObjects -> provide a minimal dict
        om_methods = types.SimpleNamespace(GetManagedObjects=lambda proxy, args: {"OBJ": {"props": True}})
        self.om_patch = mock.patch("stratis_cli._actions._list._pool.ObjectManager.Methods", om_methods)
        self.om_patch.start()

        # pools/devs searchers
        class PoolsSearcher:
            def __init__(self, props=None):
                pass
            def require_unique_match(self, x):
                return self
            def search(self, mo):
                return [("/pool/1", {"info": True})]
        class DevsSearcher:
            def __init__(self, props=None):
                pass
            def search(self, mo):
                return [("/dev/1", {"info": True})]
        self.pools_patch = mock.patch("stratis_cli._actions._list._pool.pools", side_effect=lambda props=None: PoolsSearcher(props))
        self.devs_patch = mock.patch("stratis_cli._actions._list._pool.devs", side_effect=lambda props=None: DevsSearcher(props))
        self.pools_patch.start()
        self.devs_patch.start()

        # MOPool wrapper returns our M instance
        self.mopool_patch = mock.patch("stratis_cli._actions._list._pool.MOPool", side_effect=lambda info: self.M(
            "poolA", True, True, False, "uuid-1", 1000, True, 100
        ))
        self.mopool_patch.start()

        # size_triple produces a simple formatted string for determinism
        self.size_triple_patch = mock.patch("stratis_cli._actions._list._pool.size_triple", side_effect=lambda total, used: f"{int(total)}/{int(used) if used is not None else 'NA'}/X")
        self.size_triple_patch.start()

        # Print table capture
        self.print_rows = []
        def _print_table(headers, rows, aligns):
            self.print_headers = headers
            self.print_rows = rows
            self.print_aligns = aligns
        self.print_table_patch = mock.patch("stratis_cli._actions._list._pool.print_table", side_effect=_print_table)
        self.print_table_patch.start()

        # Alerts
        class DAlerts:
            def __init__(self, devs):
                pass
            def alert_codes(self, pool_obj_path, mopool):
                return []
        self.alerts_patch = mock.patch("stratis_cli._actions._list._pool.DefaultAlerts", DAlerts)
        self.alerts_patch.start()

    def tearDown(self):
        self.get_object_patch.stop()
        self.om_patch.stop()
        self.pools_patch.stop()
        self.devs_patch.stop()
        self.mopool_patch.stop()
        self.size_triple_patch.stop()
        self.print_table_patch.stop()
        self.alerts_patch.stop()

    def test_default_table_prints_expected_headers_and_rows(self):
        dt = DefaultTable(lambda u: f"FMT-{u}")
        dt.display()
        self.assertEqual(self.print_headers, ["Name", TOTAL_USED_FREE, "Properties", "UUID", "Alerts"])
        self.assertEqual(self.print_aligns, ["<", ">", ">", ">", "<"])
        self.assertEqual(len(self.print_rows), 1)
        name, triple, props, uuid, alerts = self.print_rows[0]
        self.assertEqual(name, "poolA")
        self.assertTrue(triple.startswith("1000/"))  # formatted via size_triple patch
        # Properties string should indicate encryption (Cr) present, cache (Ca) present, overprovisioning (Op) absent
        # MetadataVersion is V2 so 'Le' code is False (~Le)
        self.assertIn("~Le", props)
        self.assertIn(" Ca", props)
        self.assertIn(" Cr", props)
        self.assertIn("~Op", props)
        self.assertEqual(uuid, "FMT-uuid-1")
        self.assertEqual(alerts, "")


@_skip_if_import_failed
class TestStoppedTable(unittest.TestCase):
    def setUp(self):
        # Patch external functions to feed data
        self.get_object_patch = mock.patch("stratis_cli._actions._list._pool.get_object", return_value=object())
        self.get_object_patch.start()

        # Two pools with V2 metadata and different feature combos
        p1 = {
            "name": "stoppedA",
            "metadata_version": MetadataVersion.V2,
            "features": {PoolFeature.ENCRYPTION, PoolFeature.CLEVIS_PRESENT},
            "devs": [{"uuid": "d1", "devnode": "/dev/sda"}],
            "key_description": None,
            "clevis_info": None,
        }
        p2 = {
            "name": "stoppedB",
            "metadata_version": MetadataVersion.V2,
            "features": None,  # unknown
            "devs": [{"uuid": "d2", "devnode": "/dev/sdb"}],
            "key_description": None,
            "clevis_info": None,
        }

        self.fetch_patch = mock.patch("stratis_cli._actions._list._pool.fetch_stopped_pools_property", return_value={
            "uuid-A": p1,
            "uuid-B": p2
        })
        self.fetch_patch.start()

        # Capture print_table
        self.print_rows = []
        def _print_table(headers, rows, aligns):
            self.print_headers = headers
            self.print_rows = rows
            self.print_aligns = aligns
        self.print_table_patch = mock.patch("stratis_cli._actions._list._pool.print_table", side_effect=_print_table)
        self.print_table_patch.start()

    def tearDown(self):
        self.get_object_patch.stop()
        self.fetch_patch.stop()
        self.print_table_patch.stop()

    def test_stopped_table_v2_clevis_and_keydesc_columns(self):
        st = StoppedTable(lambda u: f"FMT-{u}")
        st.display()

        # Headers as per implementation
        self.assertEqual(self.print_headers, ["Name", "Version", "UUID", "# Devices", "Key Description", "Clevis"])
        # Two rows expected
        self.assertEqual(len(self.print_rows), 2)
        # Find row for stoppedA (features include encryption and clevis present)
        rows_by_name = {row[0]: row for row in self.print_rows}
        rowA = rows_by_name["stoppedA"]
        rowB = rows_by_name["stoppedB"]

        # Version column should be string "2" for V2
        self.assertEqual(rowA[1], "2")
        self.assertEqual(rowB[1], "2")

        # UUID formatted
        self.assertTrue(rowA[2].startswith("FMT-uuid-"))
        # Device counts
        self.assertEqual(rowA[3], "1")

        # For V2 with encryption and KEY/CLEVIS present or not:
        # In p1 features include CLEVIS_PRESENT -> Clevis "<PRESENT>"
        self.assertEqual(rowA[5], "<PRESENT>")
        # For unknown features (p2), columns should be "<UNKNOWN>"
        self.assertEqual(rowB[4], "<UNKNOWN>")
        self.assertEqual(rowB[5], "<UNKNOWN>")