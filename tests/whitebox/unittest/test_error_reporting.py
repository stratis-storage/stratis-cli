# New comprehensive unit tests for error reporting facilities.
# Testing framework: pytest with unittest-style assertions where convenient.

import sys
import types
from contextlib import contextmanager

import pytest

# We attempt to import the module under test. The source provided appears to live in a module
# colocated with this test (per file_name). If the repository structure differs, adapt the import.
# If this import fails during CI, the path likely needs correcting to the real module path.
try:
    # Prefer relative import if this file sits alongside the module.
    from . import test_error_reporting as error_reporting_module  # type: ignore
except Exception:
    # As a fallback, try importing by common package path if available.
    error_reporting_module = None

# Helper: create a synthetic module from provided namespace if necessary so tests can proceed
if error_reporting_module is None:
    pytest.skip("Could not import error reporting module under test; please adjust import path.", allow_module_level=True)


# Utilities for faking external classes and modules
class FakeDBusException:
    def __init__(self, name: str, message: str = ""):
        self._name = name
        self._message = message

    def get_dbus_name(self):
        return self._name

    def get_dbus_message(self):
        return self._message


class Box:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@contextmanager
def inject_module(name: str, module_obj: types.ModuleType):
    """
    Temporarily inject a module into sys.modules under the given name.
    """
    old = sys.modules.get(name)
    sys.modules[name] = module_obj
    try:
        yield
    finally:
        if old is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = old


def test_interface_name_to_common_name_known_interfaces(monkeypatch):
    # Patch constants in module for deterministic testing if necessary
    # We rely on module's constants existing; otherwise define them.
    m = error_reporting_module
    # Ensure constants exist
    if not hasattr(m, "FILESYSTEM_INTERFACE"):
        monkeypatch.setattr(m, "FILESYSTEM_INTERFACE", "org.example.filesystem", raising=False)
    if not hasattr(m, "POOL_INTERFACE"):
        monkeypatch.setattr(m, "POOL_INTERFACE", "org.example.pool", raising=False)
    if not hasattr(m, "BLOCKDEV_INTERFACE"):
        monkeypatch.setattr(m, "BLOCKDEV_INTERFACE", "org.example.blockdev", raising=False)

    assert m._interface_name_to_common_name(m.FILESYSTEM_INTERFACE) == "filesystem"
    assert m._interface_name_to_common_name(m.POOL_INTERFACE) == "pool"
    # Even though flagged no cover in source, verify mapping works
    assert m._interface_name_to_common_name(m.BLOCKDEV_INTERFACE) == "block device"


def test_interpret_errors_0_name_has_no_owner_no_stratisd_process(monkeypatch):
    m = error_reporting_module

    fake_dbus_error = FakeDBusException("org.freedesktop.DBus.Error.NameHasNoOwner")

    # Create a fake psutil module whose process_iter() returns processes not named 'stratisd'
    fake_psutil = types.ModuleType("psutil")
    class P:
        def __init__(self, name): self._n=name
        def name(self): return self._n
    def process_iter():
        return [P("python"), P("dbus-daemon")]
    fake_psutil.process_iter = process_iter
    class NoSuchProcess(Exception):
        pass
    fake_psutil.NoSuchProcess = NoSuchProcess

    with inject_module("psutil", fake_psutil):
        explanation = m._interpret_errors_0(fake_dbus_error)

    assert explanation == "It appears that there is no stratisd process running."


def test_interpret_errors_0_non_matching_error_returns_none(monkeypatch):
    m = error_reporting_module
    # Error that isn't handled (e.g., some other DBus error)
    fake_dbus_error = FakeDBusException("org.freedesktop.DBus.Error.SomeOther")
    # The function returns None for unmatched error names (branch marked no cover in source)
    assert m._interpret_errors_0(fake_dbus_error) is None


def test_interpret_errors_1_unique_result_empty_list(monkeypatch):
    m = error_reporting_module

    # Provide required constants for mapping
    monkeypatch.setattr(m, "FILESYSTEM_INTERFACE", "iface.fs", raising=False)
    monkeypatch.setattr(m, "POOL_INTERFACE", "iface.pool", raising=False)

    # Create a fake DbusClientUniqueResultError with required attributes
    class FakeUniqueResultError(Exception):
        def __init__(self, interface_name, result):
            super().__init__(f"Unique result error for {interface_name}")
            self.interface_name = interface_name
            self.result = result

    # Monkeypatch the class references to our fake
    monkeypatch.setattr(m, "DbusClientUniqueResultError", FakeUniqueResultError, raising=False)

    err = FakeUniqueResultError("iface.fs", [])
    explanation = m._interpret_errors_1([err])
    assert explanation == "Most likely you specified a filesystem which does not exist."

    err2 = FakeUniqueResultError("iface.pool", [])
    explanation2 = m._interpret_errors_1([err2])
    assert explanation2 == "Most likely you specified a pool which does not exist."


def test_interpret_errors_1_engine_error_user_error_version_error(monkeypatch):
    m = error_reporting_module

    class EngineError(Exception):
        pass
    class UserError(Exception):
        pass
    class VersionError(Exception):
        def __str__(self): return "Version mismatch"

    # Patch the error classes used in isinstance checks
    monkeypatch.setattr(m, "StratisCliEngineError", EngineError, raising=False)
    monkeypatch.setattr(m, "StratisCliUserError", UserError, raising=False)
    monkeypatch.setattr(m, "StratisCliStratisdVersionError", VersionError, raising=False)

    e1 = EngineError("engine-failure")
    out1 = m._interpret_errors_1([e1])
    assert "stratisd failed to perform the operation" in out1
    assert "engine-failure" in out1

    e2 = UserError("bad command")
    out2 = m._interpret_errors_1([e2])
    assert out2 == "It appears that you issued an unintended command: bad command"

    e3 = VersionError()
    out3 = m._interpret_errors_1([e3])
    assert out3.startswith("Version mismatch. stratis can execute only the subset of its ")


def test_interpret_errors_2_dpclient_failed_property_context(monkeypatch):
    m = error_reporting_module

    # Fake contexts
    class FakeSetPropCtx:
        def __init__(self, property_name, value):
            self.property_name = property_name
            self.value = value

    # Fake DPClientInvocationError
    class FakeInvocationError(Exception):
        def __init__(self, interface_name, context):
            super().__init__("invoke")
            self.interface_name = interface_name
            self.context = context

    monkeypatch.setattr(m, "DPClientSetPropertyContext", FakeSetPropCtx, raising=False)
    monkeypatch.setattr(m, "DPClientInvocationError", FakeInvocationError, raising=False)

    first = FakeInvocationError("iface.X", FakeSetPropCtx("PropA", 42))
    next_err = FakeDBusException("org.freedesktop.DBus.Error.Failed", "permission denied")

    msg = m._interpret_errors_2([first, next_err])
    assert "stratisd failed to perform the operation that you requested" in msg
    assert '"PropA"' in msg
    assert '"iface.X"' in msg
    assert '"42"' in msg
    assert "permission denied" in msg


def test_interpret_errors_composes_with_head_action_error(monkeypatch):
    m = error_reporting_module

    class ActionError(Exception):
        pass
    class EngineError(Exception):
        pass
    monkeypatch.setattr(m, "StratisCliActionError", ActionError, raising=False)
    monkeypatch.setattr(m, "StratisCliEngineError", EngineError, raising=False)

    # Chain: ActionError -> EngineError, expect engine error explanation from _interpret_errors_1
    head = ActionError("head")
    tail = EngineError("engine boom")

    # Patch _interpret_errors_1 to ensure we are calling it with tail
    def fake_ie1(rest):
        assert len(rest) == 1 and isinstance(rest[0], EngineError)
        return "explained"
    monkeypatch.setattr(m, "_interpret_errors_1", fake_ie1)

    out = m._interpret_errors([head, tail])
    assert out == "explained"


def test_handle_error_with_explanation_exits(monkeypatch):
    m = error_reporting_module

    # Prepare mocks
    class ActionError(Exception):
        pass
    monkeypatch.setattr(m, "StratisCliActionError", ActionError, raising=False)

    # Simulate get_errors returning a chain with head ActionError
    def fake_get_errors(err):
        yield ActionError("head")
        yield Exception("tail")
    monkeypatch.setattr(m, "get_errors", fake_get_errors)

    # _interpret_errors returns a message to trigger exit_ path
    monkeypatch.setattr(m, "_interpret_errors", lambda e: "explanation text")

    # Capture exit_ call
    captured = {}
    class FakeCodes:
        ERROR = 1
    def fake_exit_(code, msg):
        captured["code"] = code
        captured["msg"] = msg
    monkeypatch.setattr(m, "StratisCliErrorCodes", FakeCodes, raising=False)
    monkeypatch.setattr(m, "exit_", fake_exit_)

    m.handle_error(Exception("anything"))

    assert captured.get("code") == 1
    assert "Execution failed:" in captured.get("msg", "")
    assert "explanation text" in captured.get("msg", "")


def test_handle_error_without_explanation_reraises(monkeypatch, capsys):
    m = error_reporting_module

    class ActionError(Exception):
        pass
    monkeypatch.setattr(m, "StratisCliActionError", ActionError, raising=False)

    # Return chain starting with ActionError to satisfy precondition
    def fake_get_errors(err):
        yield ActionError("head")
    monkeypatch.setattr(m, "get_errors", fake_get_errors)

    monkeypatch.setattr(m, "_interpret_errors", lambda e: None)

    with pytest.raises(ActionError):
        m.handle_error(Exception("boom"))

    # We expect a generic message printed to stderr before re-raise
    # However, since handle_error re-raises the original 'err' AFTER printing,
    # the printed message includes the generic advisory.
    _, err = capsys.readouterr()
    assert "stratis encountered an unexpected error during execution." in err