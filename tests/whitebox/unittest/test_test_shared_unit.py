# Copyright 2025
#
# Note on framework: These tests are written using pytest-style asserts with Python's unittest compatibility.
# If the repository uses pytest (most common), these will run as normal pytest tests.
# If stdlib unittest is used, pytest-style asserts still work under pytest runner; otherwise, they are simple assert statements.

import argparse
import importlib
import importlib.util
from types import SimpleNamespace

import pytest

# Resolve the module under test.
# It is expected to be at tests.whitebox.unittest.test_shared as per the provided path.
# We import by package path so its relative imports (.._constants, .._stratisd_constants) resolve.
mod = importlib.import_module("tests.whitebox.unittest.test_shared")

# Helper: Build a fake argparse parser and namespace quickly
def make_parser():
    return argparse.ArgumentParser(prog="test-prog", add_help=False)

def ns(**kwargs):
    return SimpleNamespace(**kwargs)

class TestUnitMap:
    def test_unit_map_all_known_units(self):
        # Using module's internal function via name (it's not exported but accessible)
        _unit_map = mod._unit_map
        assert _unit_map("B") is mod.B
        assert _unit_map("KiB") is mod.KiB
        assert _unit_map("MiB") is mod.MiB
        assert _unit_map("GiB") is mod.GiB
        assert _unit_map("TiB") is mod.TiB
        assert _unit_map("PiB") is mod.PiB

    def test_unit_map_unknown_raises_assert(self):
        _unit_map = mod._unit_map
        with pytest.raises(AssertionError):
            _unit_map("KB")  # decimal KB not supported

class TestParseRange:
    def test_parse_range_valid_values(self):
        # happy paths across units including magnitude parsing
        res_b = mod.parse_range("0B")
        assert res_b.magnitude.numerator == 0 and res_b.units is mod.B

        res_kib = mod.parse_range("1KiB")
        assert res_kib.magnitude.numerator == 1 and res_kib.units is mod.KiB

        res_mib = mod.parse_range("42MiB")
        assert res_mib.magnitude.numerator == 42 and res_mib.units is mod.MiB

        res_gib = mod.parse_range("1024GiB")
        assert res_gib.magnitude.numerator == 1024 and res_gib.units is mod.GiB

        res_tib = mod.parse_range("7TiB")
        assert res_tib.magnitude.numerator == 7 and res_tib.units is mod.TiB

        res_pib = mod.parse_range("5PiB")
        assert res_pib.magnitude.numerator == 5 and res_pib.units is mod.PiB

        # denominator must be 1 as per implementation's assertion
        assert res_pib.magnitude.denominator == 1

    @pytest.mark.parametrize(
        "value",
        [
            "", " ", "abc", "1", "1KB", "1 k i b", "1G", "1MB", "1KIB",
            "1Gi", "GiB", "MiB", "B", "-1GiB", "1.5GiB", "01GiB"
        ],
    )
    def test_parse_range_invalid_values(self, value):
        with pytest.raises(argparse.ArgumentTypeError):
            mod.parse_range(value)

class TestRejectAction:
    def test_reject_action_always_errors(self):
        parser = make_parser()
        parser.add_argument("--nope", action=mod.RejectAction, nargs=0)
        with pytest.raises(argparse.ArgumentError) as ei:
            parser.parse_args(["--nope"])
        msg = str(ei.value)
        assert "can not be assigned to or set" in msg

class TestDefaultAction:
    def test_default_action_sets_value_and_flag(self):
        parser = make_parser()
        # Emulate a defaulted option
        parser.add_argument("--opt", action=mod.DefaultAction, default="DEFAULT")
        ns = parser.parse_args(["--opt", "value"])
        assert ns.opt == "value"
        assert ns.opt_default is False

class TestEnsureNat:
    def test_ensure_nat_accepts_zero_and_positive(self):
        assert mod.ensure_nat("0") == 0
        assert mod.ensure_nat("123") == 123

    @pytest.mark.parametrize("value", ["-1", "-999999", "-0", "+-1"])
    def test_ensure_nat_rejects_negative(self, value):
        with pytest.raises(argparse.ArgumentTypeError):
            mod.ensure_nat(value)

    @pytest.mark.parametrize("value", ["abc", "1.0", "1.5", "", " ", "None"])
    def test_ensure_nat_rejects_non_int(self, value):
        with pytest.raises(argparse.ArgumentTypeError):
            mod.ensure_nat(value)

class TestMoveNotice:
    def test_move_notice_str_format(self):
        mn = mod.MoveNotice(
            name="foo",
            deprecated="old",
            preferred="new",
            version_completed="4.0.0",
        )
        s = str(mn)
        assert 'MOVE NOTICE:' in s
        assert '"foo"' in s
        assert '"old foo"' in s
        assert '"new"' in s
        assert "4.0.0" in s

class TestClevisEncryptionOptions:
    def _make_namespace(self, **kwargs):
        # Provide all expected attrs with defaults as argparse would
        base = dict(
            clevis=None,
            thumbprint=None,
            tang_url=None,
            trust_url=False,
        )
        base.update(kwargs)
        return SimpleNamespace(**base)

    def _make_parser(self):
        return argparse.ArgumentParser(prog="test", add_help=False)

    def test_requires_tang_url_when_clevis_tang_or_nbde(self):
        parser = self._make_parser()
        n = self._make_namespace(clevis=mod.Clevis.TANG, tang_url=None)
        ceo = mod.ClevisEncryptionOptions(n)
        with pytest.raises(SystemExit) as ei:
            ceo.verify(n, parser)
        assert ei.value.code != 0

        parser = self._make_parser()
        n = self._make_namespace(clevis=mod.Clevis.NBDE, tang_url=None)
        ceo = mod.ClevisEncryptionOptions(n)
        with pytest.raises(SystemExit):
            ceo.verify(n, parser)

    def test_requires_thumbprint_or_trust_when_tang_url_specified(self):
        parser = self._make_parser()
        n = self._make_namespace(clevis=mod.Clevis.TANG, tang_url="https://tang/", thumbprint=None, trust_url=False)
        ceo = mod.ClevisEncryptionOptions(n)
        with pytest.raises(SystemExit):
            ceo.verify(n, parser)

    def test_requires_clevis_method_if_tang_url_specified(self):
        parser = self._make_parser()
        n = self._make_namespace(clevis=None, tang_url="https://tang/", thumbprint="abc", trust_url=False)
        ceo = mod.ClevisEncryptionOptions(n)
        with pytest.raises(SystemExit):
            ceo.verify(n, parser)

    def test_requires_tang_url_if_trust_or_thumbprint_specified(self):
        parser = self._make_parser()
        n = self._make_namespace(clevis=None, tang_url=None, thumbprint="abc", trust_url=False)
        ceo = mod.ClevisEncryptionOptions(n)
        with pytest.raises(SystemExit):
            ceo.verify(n, parser)

        parser = self._make_parser()
        n = self._make_namespace(clevis=None, tang_url=None, thumbprint=None, trust_url=True)
        ceo = mod.ClevisEncryptionOptions(n)
        with pytest.raises(SystemExit):
            ceo.verify(n, parser)

    def test_sets_namespace_clevis_none_when_no_binding(self):
        parser = self._make_parser()
        n = self._make_namespace(clevis=None, tang_url=None)
        ceo = mod.ClevisEncryptionOptions(n)
        ceo.verify(n, parser)
        assert n.clevis is None

    def test_sets_namespace_clevis_tpm2_when_clevis_tpm2(self):
        parser = self._make_parser()
        n = self._make_namespace(clevis=mod.Clevis.TPM2, tang_url=None)
        ceo = mod.ClevisEncryptionOptions(n)
        ceo.verify(n, parser)
        assert isinstance(n.clevis, mod.ClevisInfo)
        assert n.clevis.pin == mod.CLEVIS_PIN_TPM2
        assert n.clevis.config == {}

    def test_sets_namespace_clevis_tang_with_thumbprint(self):
        parser = self._make_parser()
        n = self._make_namespace(
            clevis=mod.Clevis.TANG,
            tang_url="http://example",
            thumbprint="deadbeef",
            trust_url=False,
        )
        ceo = mod.ClevisEncryptionOptions(n)
        ceo.verify(n, parser)
        assert isinstance(n.clevis, mod.ClevisInfo)
        assert n.clevis.pin == mod.CLEVIS_PIN_TANG
        # Expect config to include URL and thumbprint
        assert n.clevis.config.get(mod.CLEVIS_KEY_URL) == "http://example"
        assert mod.CLEVIS_KEY_THP in n.clevis.config
        assert mod.CLEVIS_KEY_TANG_TRUST_URL not in n.clevis.config

    def test_sets_namespace_clevis_tang_with_trust_url(self):
        parser = self._make_parser()
        n = self._make_namespace(
            clevis=mod.Clevis.NBDE,
            tang_url="http://example",
            thumbprint=None,
            trust_url=True,
        )
        ceo = mod.ClevisEncryptionOptions(n)
        ceo.verify(n, parser)
        assert isinstance(n.clevis, mod.ClevisInfo)
        assert n.clevis.pin == mod.CLEVIS_PIN_TANG
        assert n.clevis.config.get(mod.CLEVIS_KEY_URL) == "http://example"
        assert n.clevis.config.get(mod.CLEVIS_KEY_TANG_TRUST_URL) is True
        assert mod.CLEVIS_KEY_THP not in n.clevis.config

    def test_constructor_removes_original_attributes_from_namespace(self):
        # Validate that __init__ deletes clevis-related fields from the namespace
        base = self._make_namespace(clevis=mod.Clevis.TANG, thumbprint="abc", tang_url="u", trust_url=True)
        # Keep a copy of keys before
        before_keys = set(vars(base).keys())
        ceo = mod.ClevisEncryptionOptions(base)
        after_keys = set(vars(base).keys())
        # Verify deletion while ceo kept copies internally
        assert {"clevis", "thumbprint", "tang_url", "trust_url"}.issubset(before_keys)
        assert {"clevis", "thumbprint", "tang_url", "trust_url"}.isdisjoint(after_keys)
        # And verify that verify() reattaches processed 'clevis' back to namespace
        parser = self._make_parser()
        n = self._make_namespace(clevis=mod.Clevis.TANG, thumbprint="abc", tang_url="u", trust_url=False)
        ceo = mod.ClevisEncryptionOptions(n)
        ceo.verify(n, parser)
        assert hasattr(n, "clevis")