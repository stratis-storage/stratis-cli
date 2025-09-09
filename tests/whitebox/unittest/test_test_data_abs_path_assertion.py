# Testing library and framework: pytest (with built-in assertions). These tests avoid external dependencies by using a dummy class shape.
import importlib
import importlib.util
import os
import sys
import types

import pytest


def _import_test_data_module():
    """
    Import the module under test (tests.whitebox.unittest.test_data) safely by
    priming sys.modules['stratis_cli'] with a dummy that has 'run' attribute,
    to satisfy the import-time assertion.
    """
    # If already imported, just return it
    modname = "tests.whitebox.unittest.test_data"
    if modname in sys.modules:
        return sys.modules[modname]

    # Ensure a dummy stratis_cli with attribute run is present for the assertion
    dummy = types.SimpleNamespace(run=lambda: None)
    sys.modules.setdefault("stratis_cli", dummy)

    return importlib.import_module(modname)


def test__add_abs_path_assertion_happy_path_calls_original_method(monkeypatch):
    """
    Ensures that when all paths are absolute, the wrapper delegates to the original method
    and returns its result unchanged.
    """
    test_data = _import_test_data_module()
    _add_abs_path_assertion = test_data._add_abs_path_assertion

    calls = []

    class DummyMethods:
        def Target(self, proxy, args):
            calls.append(("Target", proxy, args))
            return "OK:" + ",".join(args["devices"])

    class DummyKlass:
        class Methods(DummyMethods):
            pass

    # Apply wrapper
    _add_abs_path_assertion(DummyKlass, "Target", "devices")

    # Build absolute paths
    abs1 = os.path.abspath("/dev/sda")
    abs2 = os.path.abspath("/dev/sdb")
    args = {"devices": [abs1, abs2]}

    # Call through the wrapped method
    result = DummyKlass.Methods().Target(proxy="proxy-obj", args=args)

    # Expectations
    assert result == f"OK:{abs1},{abs2}"
    assert calls and calls[0][0] == "Target"
    assert calls[0][1] == "proxy-obj"
    assert calls[0][2] is args  # same dict passed through


def test__add_abs_path_assertion_raises_on_relative_paths(monkeypatch):
    """
    Ensures that any relative path causes an assertion error with a clear message listing offending paths.
    """
    test_data = _import_test_data_module()
    _add_abs_path_assertion = test_data._add_abs_path_assertion

    class DummyMethods:
        def Target(self, proxy, args):
            return "SHOULD NOT REACH"

    class DummyKlass:
        class Methods(DummyMethods):
            pass

    _add_abs_path_assertion(DummyKlass, "Target", "devices")

    rel1 = "relative/dev1"
    abs1 = os.path.abspath("/dev/sda")
    rel2 = "./dev2"
    args = {"devices": [rel1, abs1, rel2]}

    with pytest.raises(AssertionError) as ei:
        DummyKlass.Methods().Target(proxy=None, args=args)

    msg = str(ei.value)
    # Check it mentions both relative paths and the general precondition string
    assert "Precondition violated: paths" in msg
    assert "relative/dev1" in msg
    assert "./dev2" in msg


def test__add_abs_path_assertion_allows_empty_device_list(monkeypatch):
    """
    An empty list should be permitted (no relative paths).
    """
    test_data = _import_test_data_module()
    _add_abs_path_assertion = test_data._add_abs_path_assertion

    class DummyMethods:
        def Target(self, proxy, args):
            return "EMPTY OK"

    class DummyKlass:
        class Methods(DummyMethods):
            pass

    _add_abs_path_assertion(DummyKlass, "Target", "devices")

    args = {"devices": []}
    result = DummyKlass.Methods().Target(proxy=None, args=args)
    assert result == "EMPTY OK"


def test__add_abs_path_assertion_mixed_relative_absolute(monkeypatch):
    """
    Mixed absolute/relative should still assert before invoking original method.
    """
    test_data = _import_test_data_module()
    _add_abs_path_assertion = test_data._add_abs_path_assertion

    called = False

    class DummyMethods:
        def Target(self, proxy, args):
            nonlocal called
            called = True
            return "OK"

    class DummyKlass:
        class Methods(DummyMethods):
            pass

    _add_abs_path_assertion(DummyKlass, "Target", "devices")

    args = {"devices": [os.path.abspath("/dev/sda"), "relpath"]}
    with pytest.raises(AssertionError):
        DummyKlass.Methods().Target(proxy=None, args=args)

    assert called is False


def test__add_abs_path_assertion_different_key(monkeypatch):
    """
    Validate that the key parameter determines where to look for paths.
    """
    test_data = _import_test_data_module()
    _add_abs_path_assertion = test_data._add_abs_path_assertion

    seen = {}

    class DummyMethods:
        def Target(self, proxy, args):
            # Ensure the args come through untouched and original method runs
            seen["args"] = dict(args)
            return "ALTKEY OK"

    class DummyKlass:
        class Methods(DummyMethods):
            pass

    _add_abs_path_assertion(DummyKlass, "Target", "paths")

    args = {"paths": [os.path.abspath("/dev/sdc")], "devices": ["rel-ignored"]}
    out = DummyKlass.Methods().Target(proxy="px", args=args)
    assert out == "ALTKEY OK"
    assert seen["args"] == args


def test__add_abs_path_assertion_error_message_formatting_single(monkeypatch):
    """
    Verify singular offending path is formatted correctly in the error message.
    """
    test_data = _import_test_data_module()
    _add_abs_path_assertion = test_data._add_abs_path_assertion

    class DummyMethods:
        def Target(self, proxy, args):
            return "OK"

    class DummyKlass:
        class Methods(DummyMethods):
            pass

    _add_abs_path_assertion(DummyKlass, "Target", "devices")

    args = {"devices": ["relative_only"]}
    with pytest.raises(AssertionError) as ei:
        DummyKlass.Methods().Target(proxy=None, args=args)

    msg = str(ei.value)
    # Ensure the offending relative path is included verbatim
    assert "relative_only" in msg


def test__add_abs_path_assertion_method_replacement_is_idempotent(monkeypatch):
    """
    Applying the wrapper multiple times should continue to enforce the check and delegate ultimately to the original.
    """
    test_data = _import_test_data_module()
    _add_abs_path_assertion = test_data._add_abs_path_assertion

    call_count = 0

    class DummyMethods:
        def Target(self, proxy, args):
            nonlocal call_count
            call_count += 1
            return "OK"

    class DummyKlass:
        class Methods(DummyMethods):
            pass

    _add_abs_path_assertion(DummyKlass, "Target", "devices")
    _add_abs_path_assertion(DummyKlass, "Target", "devices")  # apply twice

    args = {"devices": [os.path.abspath("/dev/sda")]}
    out = DummyKlass.Methods().Target(proxy=None, args=args)
    assert out == "OK"
    assert call_count == 1  # should reach the original exactly once


def test_import_time_assertion_on_stratis_cli_presence(monkeypatch):
    """
    Ensure the module import succeeds when a dummy 'stratis_cli' module with a 'run' attribute exists.
    """
    # Remove cached modules to simulate a fresh import
    for name in list(sys.modules.keys()):
        if name in ("tests.whitebox.unittest.test_data",):
            sys.modules.pop(name, None)

    dummy = types.SimpleNamespace(run=lambda: None)
    sys.modules["stratis_cli"] = dummy

    mod = importlib.import_module("tests.whitebox.unittest.test_data")
    assert hasattr(sys.modules.get("stratis_cli"), "run")
    # Sanity: verify the function is present
    assert hasattr(mod, "_add_abs_path_assertion")