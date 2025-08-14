# Note: Testing library/framework used: pytest with monkeypatch and tmp_path fixtures.
# These tests focus on the public behavior of utility constructs defined in the utils module.
# They mock external dependencies like dbus and termios to ensure isolation.

import importlib
import io
import os
import sys
import errno
import builtins
from types import SimpleNamespace
from contextlib import contextmanager

import pytest

# Attempt to import the module under test.
# The file under review contains symbols like: get_pass, get_passphrase_fd, Device, PoolFeature,
# StoppedPool, get_errors, long_running_operation, fetch_stopped_pools_property.
#
# We will try to import via two strategies:
# 1) Direct package import if available per project structure (e.g., stratis_cli._utils or similar).
# 2) Fallback to dynamic import from tests/whitebox/unittest/test_utils.py
#
# Strategy 2 is provided to make the tests resilient to the context presented in this PR.

CANDIDATE_MODULE_NAMES = [
    # Common likely locations; adjust according to repository structure if necessary.
    "stratis_cli._utils",
    "stratis_cli._actions._utils",
    "src.stratis_cli._utils",
]

_utils = None
_import_error_notes = []

for name in CANDIDATE_MODULE_NAMES:
    try:
        _utils = importlib.import_module(name)
        break
    except Exception as e:
        _import_error_notes.append((name, repr(e)))

if _utils is None:
    # Fallback: attempt to import the given path as a module by spec from file.
    import importlib.util
    fallback_path = os.path.join("tests", "whitebox", "unittest", "test_utils.py")
    if os.path.exists(fallback_path):
        spec = importlib.util.spec_from_file_location("utils_under_test", fallback_path)
        _utils = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(_utils)  # type: ignore[attr-defined]
        except Exception as e:
            raise RuntimeError(
                f"Failed to import utils from fallback path {fallback_path}; "
                f"prior attempts: {_import_error_notes}; error: {e}"
            ) from e
    else:
        raise RuntimeError(
            "Could not locate the utils module to test. "
            f"Attempted names: {CANDIDATE_MODULE_NAMES}; "
            f"fallback path missing: {fallback_path}"
        )

# Helpers to reload module with modified environment
@contextmanager
def reloaded_utils_with_env(**env_updates):
    prev = {k: os.environ.get(k) for k in env_updates}
    try:
        for k, v in env_updates.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = str(v)
        # Force reload to re-evaluate _STRICT_POOL_FEATURES
        importlib.reload(_utils)
        yield _utils
    finally:
        for k, v in prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        importlib.reload(_utils)

# ---- Tests for get_pass ----

def test_get_pass_reads_line_and_strips(monkeypatch, capsys):
    inp = io.StringIO("secret-pass\n")
    monkeypatch.setattr(sys, "stdin", inp, raising=False)
    # termios operations are guarded; ensure they don't blow up if attempted
    monkeypatch.setattr(_utils.termios, "tcgetattr", lambda x: (_ for _ in ()).throw(_utils.termios.error(0, "no tty")), raising=True)
    monkeypatch.setattr(_utils.termios, "tcsetattr", lambda *args, **kwargs: None, raising=True)

    result = _utils.get_pass("Prompt: ")
    captured = capsys.readouterr()
    assert captured.out.startswith("Prompt: ")
    assert result == "secret-pass"

def test_get_pass_handles_non_tty_warning(monkeypatch, capsys):
    inp = io.StringIO("abc\n")
    monkeypatch.setattr(sys, "stdin", inp, raising=False)

    class FakeErr(Exception):
        def __init__(self):
            self.args = (errno.ENOTTY,)
    import errno as _errno
    # cause termios.tcgetattr to raise termios.error with ENOTTY
    monkeypatch.setattr(_utils, "errno", _errno, raising=False)
    def raise_notty(_):
        err = _utils.termios.error()
        err.args = (_errno.ENOTTY,)
        raise err
    monkeypatch.setattr(_utils.termios, "tcgetattr", raise_notty, raising=True)
    monkeypatch.setattr(_utils.termios, "tcsetattr", lambda *args, **kwargs: None, raising=True)

    result = _utils.get_pass("Enter: ")
    captured = capsys.readouterr()
    assert "not a TTY" in captured.err
    assert result == "abc"

# ---- Tests for get_passphrase_fd ----

def test_get_passphrase_fd_from_stdin_happy_path(monkeypatch):
    # Passwords match and non-empty
    stdin_data = "p@ssw0rd\np@ssw0rd\n"
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_data), raising=False)
    # Ensure termios does not interfere
    monkeypatch.setattr(_utils.termios, "tcgetattr", lambda x: (_ for _ in ()).throw(_utils.termios.error(0, "fail")), raising=True)
    monkeypatch.setattr(_utils.termios, "tcsetattr", lambda *args, **kwargs: None, raising=True)

    fd_read, fd_close = _utils.get_passphrase_fd(keyfile_path=None, verify=True)
    try:
        assert isinstance(fd_read, int) and isinstance(fd_close, int)
        assert fd_read != fd_close  # read and write ends of the pipe
        # Read back from the read end to verify content
        data = os.read(fd_read, 1024).decode("utf-8")
        assert data == "p@ssw0rd"
    finally:
        os.close(fd_close)
        os.close(fd_read)

def test_get_passphrase_fd_from_stdin_mismatch_raises(monkeypatch):
    stdin_data = "one\nTWO\n"
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_data), raising=False)
    monkeypatch.setattr(_utils.termios, "tcgetattr", lambda x: (_ for _ in ()).throw(_utils.termios.error(0, "fail")), raising=True)
    monkeypatch.setattr(_utils.termios, "tcsetattr", lambda *args, **kwargs: None, raising=True)

    with pytest.raises(_utils.StratisCliPassphraseMismatchError):
        _utils.get_passphrase_fd(keyfile_path=None, verify=True)

def test_get_passphrase_fd_from_stdin_empty_raises(monkeypatch):
    stdin_data = "\n\n"
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_data), raising=False)
    monkeypatch.setattr(_utils.termios, "tcgetattr", lambda x: (_ for _ in ()).throw(_utils.termios.error(0, "fail")), raising=True)
    monkeypatch.setattr(_utils.termios, "tcsetattr", lambda *args, **kwargs: None, raising=True)

    with pytest.raises(_utils.StratisCliPassphraseEmptyError):
        _utils.get_passphrase_fd(keyfile_path=None, verify=True)

def test_get_passphrase_fd_keyfile_happy_path(tmp_path):
    p = tmp_path / "keyfile.txt"
    p.write_text("abc123", encoding="utf-8")
    fd_read, fd_close = _utils.get_passphrase_fd(keyfile_path=str(p), verify=False)
    try:
        assert fd_read == fd_close
        # Sanity: os.read works and reads the file bytes if used downstream
        os.lseek(fd_read, 0, os.SEEK_SET)
        data = os.read(fd_read, 6).decode("utf-8")
        assert data == "abc123"
    finally:
        os.close(fd_read)

def test_get_passphrase_fd_keyfile_missing_raises(tmp_path):
    missing = tmp_path / "missing_key"
    with pytest.raises(_utils.StratisCliKeyfileNotFoundError):
        _utils.get_passphrase_fd(keyfile_path=str(missing), verify=False)

# ---- Tests for Device ----

def test_device_initialization_from_mapping():
    dev = _utils.Device({"uuid": "9b2b6f08-7b59-4e8c-8e3d-65f63d4d5e97", "devnode": "/dev/sda"})
    assert str(dev.uuid) == "9b2b6f08-7b59-4e8c-8e3d-65f63d4d5e97"
    assert dev.devnode == "/dev/sda"

# ---- Tests for PoolFeature ----

def test_pool_feature_str_and_unrecognized():
    assert str(_utils.PoolFeature.ENCRYPTION) == "encryption"
    assert str(_utils.PoolFeature.UNRECOGNIZED) == "<UNRECOGNIZED>"

def test_pool_feature_missing_strict_vs_non_strict(monkeypatch):
    # Non-strict: unknown value -> UNRECOGNIZED (per _missing_ branch)
    with reloaded_utils_with_env(STRATIS_STRICT_POOL_FEATURES=None) as mod:
        val = mod.PoolFeature("unknown")  # type: ignore[arg-type]
        assert val is mod.PoolFeature.UNRECOGNIZED

    # Strict: should defer to Enum default which returns None (ValueError on creation)
    with reloaded_utils_with_env(STRATIS_STRICT_POOL_FEATURES=1) as mod, pytest.raises(ValueError):
        mod.PoolFeature("not-a-feature")  # type: ignore[arg-type]

# ---- Tests for StoppedPool ----

def test_stopped_pool_parses_all_fields_happy_path(monkeypatch):
    # Prepare a realistic mapping
    pool_info = {
        "devs": [
            {"uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "devnode": "/dev/sda"},
            {"uuid": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "devnode": "/dev/sdb"},
        ],
        "clevis_info": (True, (False, None)),  # consistent, not encrypted -> None value
        "key_description": (True, (True, "mykey")),  # consistent, encrypted set -> string in subclass
        "name": "pooly",
        "metadata_version": (True, 2),
        "features": (True, ["encryption", "raid", "unknown-feature"]),
    }
    sp = _utils.StoppedPool(pool_info)
    # devices parsed
    assert len(sp.devs) == 2
    assert sp.devs[0].devnode == "/dev/sda"
    # clevis_info present but value None due to not encrypted
    assert sp.clevis_info is not None
    assert getattr(sp.clevis_info, "value", None) is None
    # key_description parsed to string in subclass when set
    assert sp.key_description is not None
    assert sp.key_description.value == "mykey"
    # name
    assert sp.name == "pooly"
    # metadata version wrapped
    assert sp.metadata_version is not None
    assert sp.metadata_version.value == 2 if hasattr(sp.metadata_version, "value") else int(sp.metadata_version)
    # features: includes recognized and an UNRECOGNIZED element
    assert sp.features is not None
    feature_names = {str(f) for f in sp.features}
    assert "encryption" in feature_names
    assert "raid" in feature_names
    assert "<UNRECOGNIZED>" in feature_names

def test_stopped_pool_handles_invalid_metadata_version(monkeypatch):
    pool_info = {
        "devs": [],
        "metadata_version": (True, "not-an-int"),
        "features": (False, []),
    }
    sp = _utils.StoppedPool(pool_info)
    # ValueError path sets metadata_version to None (guarded by pragma on except but behavior is sane)
    assert sp.metadata_version is None
    assert sp.features is None

# ---- Tests for get_errors ----

def test_get_errors_yields_chain():
    base = ValueError("base")
    mid = RuntimeError("mid")
    mid.__cause__ = base  # type: ignore[attr-defined]
    top = Exception("top")
    top.__cause__ = mid  # type: ignore[attr-defined]

    chain = list(_utils.get_errors(top))
    assert [type(e) for e in chain] == [Exception, RuntimeError, ValueError]

def test_get_errors_uses_context_when_no_cause():
    base = ValueError("base")
    mid = RuntimeError("mid")
    mid.__context__ = base  # type: ignore[attr-defined]
    top = Exception("top")
    top.__context__ = mid  # type: ignore[attr-defined]

    chain = list(_utils.get_errors(top))
    assert [type(e) for e in chain] == [Exception, RuntimeError, ValueError]

# ---- Tests for long_running_operation ----

class DummyDBusException(Exception):
    def get_dbus_name(self):
        return "org.freedesktop.DBus.Error.NoReply"

def test_long_running_operation_swallows_no_reply(monkeypatch):
    # Build a fake DPClientInvocationError carrying a DBusException in the chain
    class FakeInvocationError(_utils.DPClientInvocationError):  # type: ignore
        pass

    no_reply = DummyDBusException()
    err = FakeInvocationError("boom")
    # Chain through __cause__
    err.__cause__ = no_reply  # type: ignore[attr-defined]

    # Replace DBusException type check to accept our dummy
    monkeypatch.setattr(_utils, "DBusException", DummyDBusException, raising=False)

    called = {"count": 0}
    def fn(ns):
        called["count"] += 1
        raise err

    wrapped = _utils.long_running_operation(fn)
    # Should not raise due to NoReply
    wrapped(SimpleNamespace())
    assert called["count"] == 1

def test_long_running_operation_re_raises_other_errors(monkeypatch):
    class FakeInvocationError(_utils.DPClientInvocationError):  # type: ignore
        pass

    other = Exception("other")
    err = FakeInvocationError("boom")
    err.__cause__ = other  # type: ignore[attr-defined]

    # Ensure DBusException check will not consider 'other' a DBusException
    monkeypatch.setattr(_utils, "DBusException", DummyDBusException, raising=False)

    def fn(ns):
        raise err

    wrapped = _utils.long_running_operation(fn)
    with pytest.raises(FakeInvocationError):
        wrapped(SimpleNamespace())

# ---- Tests for fetch_stopped_pools_property ----

def test_fetch_stopped_pools_property_calls_Manager(monkeypatch):
    # Build a sentinel proxy and a fake Manager.Properties.StoppedPools.Get
    sentinel = object()

    class FakeStoppedPools:
        @staticmethod
        def Get(proxy):
            assert proxy is sentinel
            return {"ok": True}

    class FakeProps:
        StoppedPools = FakeStoppedPools()

    class FakeManager:
        Properties = FakeProps()

    # Patch the module import inside fetch_stopped_pools_property
    # The function imports ". _data Manager" inside it; simulate that.
    class FakeDataModule:
        Manager = FakeManager

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == _utils.__package__ + "._data" or name.endswith("._data"):
            return FakeDataModule
        return original_import(name, globals, locals, fromlist, level)

    original_import = __import__
    monkeypatch.setattr(builtins, "__import__", fake_import, raising=True)

    result = _utils.fetch_stopped_pools_property(sentinel)
    assert result == {"ok": True}