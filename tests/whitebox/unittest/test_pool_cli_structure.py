# Unit tests for pool CLI options & structures.
# Testing framework: unittest (standard library).
#
# These tests focus on:
# - IntegrityOptions.verify conditional behavior and namespace effects
# - CreateOptions.verify delegation to sub-verifiers
# - Structural validation of POOL_SUBCMDS for key subcommands and argument specs

import unittest
from unittest.mock import patch
import copy
from argparse import ArgumentParser, Namespace
import importlib.util
import pathlib

# Load the module under test by path. The file lives next to this test file.
MODULE_PATH = pathlib.Path(__file__).with_name("test_pool.py")
pool_mod = None
if MODULE_PATH.exists():
    spec = importlib.util.spec_from_file_location("pool_mod", MODULE_PATH)
    pool_mod = importlib.util.module_from_spec(spec)  # type: ignore[assignment]
    assert spec.loader is not None
    spec.loader.exec_module(pool_mod)  # type: ignore[arg-type]

# Import frequently used symbols when available to keep tests concise.
if pool_mod is not None:
    IntegrityOption = pool_mod.IntegrityOption
    IntegrityTagSpec = pool_mod.IntegrityTagSpec
    Range = pool_mod.Range
    MiB = pool_mod.MiB

def _make_parser():
    # ArgumentParser.error() invokes sys.exit(), which raises SystemExit
    return ArgumentParser(prog="stratis", add_help=False)

@unittest.skipUnless(pool_mod is not None, "pool module not present on this branch")
class IntegrityOptionsVerifyTestCase(unittest.TestCase):
    def test_no_integrity_with_non_default_journal_size_errors(self):
        parser = _make_parser()
        namespace = Namespace(
            integrity=IntegrityOption.NO,
            journal_size=Range(64, MiB),
            journal_size_default=False,
            tag_spec=IntegrityTagSpec.B512,
            tag_spec_default=True,
        )
        opts = pool_mod.IntegrityOptions(copy.copy(namespace))
        with self.assertRaises(SystemExit):
            opts.verify(namespace, parser)

    def test_no_integrity_with_non_default_tag_spec_errors(self):
        parser = _make_parser()
        namespace = Namespace(
            integrity=IntegrityOption.NO,
            journal_size=Range(128, MiB),
            journal_size_default=True,
            tag_spec=IntegrityTagSpec.B256,
            tag_spec_default=False,
        )
        opts = pool_mod.IntegrityOptions(copy.copy(namespace))
        with self.assertRaises(SystemExit):
            opts.verify(namespace, parser)

    def test_preallocate_with_overrides_is_ok_and_sets_back_on_namespace(self):
        parser = _make_parser()
        namespace = Namespace(
            integrity=IntegrityOption.PRE_ALLOCATE,
            journal_size=Range(256, MiB),
            journal_size_default=False,
            tag_spec=IntegrityTagSpec.B512,
            tag_spec_default=False,
        )
        opts = pool_mod.IntegrityOptions(copy.copy(namespace))
        # Should not error
        opts.verify(namespace, parser)
        # verify() sets namespace.integrity to the IntegrityOptions instance
        self.assertIs(namespace.integrity, opts)

    def test_default_flags_missing_use_true_and_no_error(self):
        # __init__ defaults journal_size_default/tag_spec_default to True if not present
        parser = _make_parser()
        namespace = Namespace(
            integrity=IntegrityOption.NO,
            journal_size=Range(128, MiB),
            tag_spec=IntegrityTagSpec.B512,
        )
        opts = pool_mod.IntegrityOptions(copy.copy(namespace))
        self.assertTrue(opts.journal_size_default)
        self.assertTrue(opts.tag_spec_default)
        # With both defaults True, verify should be OK even with NO integrity
        opts.verify(namespace, parser)
        self.assertIs(namespace.integrity, opts)

@unittest.skipUnless(pool_mod is not None, "pool module not present on this branch")
class CreateOptionsVerifyTestCase(unittest.TestCase):
    def test_verify_invokes_sub_verifiers(self):
        called = {"clevis": False, "integrity": False}

        def fake_clevis(ns):
            class _Dummy:
                def verify(self, namespace, parser):
                    called["clevis"] = True
            return _Dummy()

        def fake_integrity(ns):
            class _Dummy:
                def verify(self, namespace, parser):
                    called["integrity"] = True
            return _Dummy()

        with patch.object(pool_mod, "ClevisEncryptionOptions", new=fake_clevis), \
             patch.object(pool_mod, "IntegrityOptions", new=fake_integrity):
            create_opts = pool_mod.CreateOptions(Namespace(dummy=True))
            parser = _make_parser()
            namespace = Namespace()
            create_opts.verify(namespace, parser)

        self.assertTrue(called["clevis"])
        self.assertTrue(called["integrity"])

@unittest.skipUnless(pool_mod is not None, "pool module not present on this branch")
class PoolSubcommandsShapeTestCase(unittest.TestCase):
    def _find_subcmd(self, name):
        for sub in pool_mod.POOL_SUBCMDS:
            if sub[0] == name:
                return sub[1]
        return None

    def test_has_expected_top_level_subcommands(self):
        names = [name for name, _ in pool_mod.POOL_SUBCMDS]
        expected = {
            "create", "destroy", "start", "stop", "list", "rename", "encryption",
            "init-cache", "add-data", "add-cache", "extend-data", "bind", "rebind",
            "unbind", "set-fs-limit", "overprovision", "explain", "debug",
        }
        missing = expected - set(names)
        self.assertFalse(missing, f"Missing subcommands: {missing}")

    def test_create_integrity_group_defaults_and_choices(self):
        sub = self._find_subcmd("create")
        self.assertIsNotNone(sub)
        groups = sub.get("groups", [])
        integrity_group = None
        for title, cfg in groups:
            if title == "Integrity":
                integrity_group = cfg
                break
        self.assertIsNotNone(integrity_group, "Integrity group not found in create")
        args = dict(integrity_group["args"])
        # --integrity argument properties

        integrity_arg = args.get("--integrity")
        self.assertIsNotNone(integrity_arg)
        self.assertIn(IntegrityOption.PRE_ALLOCATE, integrity_arg["choices"])
        self.assertEqual(integrity_arg["default"], IntegrityOption.PRE_ALLOCATE)
        self.assertIs(integrity_arg["type"], pool_mod.IntegrityOption)
        # --journal-size argument defaults
        journal_arg = args.get("--journal-size")
        self.assertIsNotNone(journal_arg)
        self.assertEqual(journal_arg["default"], Range(128, MiB))
        self.assertIs(journal_arg["type"], pool_mod.parse_range)
        self.assertIs(journal_arg["action"], pool_mod.DefaultAction)
        # --tag-spec argument
        tag_arg = args.get("--tag-spec")
        self.assertIsNotNone(tag_arg)
        self.assertEqual(tag_arg["default"], pool_mod.IntegrityTagSpec.B512)
        self.assertNotIn(pool_mod.IntegrityTagSpec.B0, tag_arg["choices"])

    def test_start_unlock_method_group_has_expected_types(self):
        sub = self._find_subcmd("start")
        self.assertIsNotNone(sub)
        groups = sub.get("groups", [])
        found = False
        for title, cfg in groups:
            if title == "Optional Unlock Method":
                found = True
                mea = cfg["mut_ex_args"]
                self.assertIsInstance(mea, list)
                self.assertTrue(mea)
                _, args_list = mea[0]
                unlock_name, unlock_cfg = args_list[0]
                self.assertEqual(unlock_name, "--unlock-method")
                self.assertIs(unlock_cfg["type"], pool_mod.UnlockMethod)
                self.assertEqual(set(unlock_cfg["choices"]), set(pool_mod.UnlockMethod))
                token_name, token_cfg = args_list[1]
                self.assertEqual(token_name, "--token-slot")
                self.assertIs(token_cfg["type"], pool_mod.ensure_nat)
                break
        self.assertTrue(found, "Optional Unlock Method group not found in start subcommand")

    def test_unbind_method_argument_choices(self):
        sub = self._find_subcmd("unbind")
        self.assertIsNotNone(sub)
        # args is a list of (name, cfg) pairs; convert to dict for inspection
        args_map = dict(sub["args"])
        method_cfg = args_map["method"]
        self.assertEqual(set(method_cfg["choices"]), set(pool_mod.EncryptionMethod))
        self.assertIs(method_cfg["type"], pool_mod.EncryptionMethod)

@unittest.skipUnless(pool_mod is not None, "pool module not present on this branch")
class IntegrityOptionsMatrixTestCase(unittest.TestCase):
    def test_matrix(self):
        scenarios = [
            # (integrity, journal_default, tag_default, should_exit)
            (IntegrityOption.NO, False, True, True),
            (IntegrityOption.NO, True, False, True),
            (IntegrityOption.NO, True, True, False),
            (IntegrityOption.PRE_ALLOCATE, False, False, False),
        ]
        for integrity, j_def, t_def, should_exit in scenarios:
            with self.subTest(integrity=integrity, journal_default=j_def, tag_default=t_def):
                parser = ArgumentParser(add_help=False)
                namespace = Namespace(
                    integrity=integrity,
                    journal_size=Range(128, MiB),
                    journal_size_default=j_def,
                    tag_spec=IntegrityTagSpec.B512,
                    tag_spec_default=t_def,
                )
                opts = pool_mod.IntegrityOptions(copy.copy(namespace))
                if should_exit:
                    with self.assertRaises(SystemExit):
                        opts.verify(namespace, parser)
                else:
                    opts.verify(namespace, parser)
                    self.assertIs(namespace.integrity, opts)

if __name__ == "__main__":
    unittest.main()