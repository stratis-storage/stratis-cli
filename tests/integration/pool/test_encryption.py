# Copyright 2025 Red Hat, Inc.
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
Test 'encryption'.
"""

# isort: LOCAL
from stratis_cli import StratisCliErrorCodes
from stratis_cli._errors import (
    StratisCliEngineError,
    StratisCliInPlaceNotSpecified,
    StratisCliNoChangeError,
)

from .._keyutils import RandomKeyTmpFile
from .._misc import RUNNER, TEST_RUNNER, SimTestCase, device_name_list

_ERROR = StratisCliErrorCodes.ERROR
_DEVICE_STRATEGY = device_name_list(1, 1)


class BindTestCase(SimTestCase):
    """
    Test 'bind' on a sim pool.
    """

    _MENU = ["--propagate", "pool", "encryption", "bind"]
    _POOLNAME = "poolname"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_bind_when_unencrypted_tang(self):
        """
        Binding when unencrypted with tang should return an error.
        """
        command_line = self._MENU + [
            "nbde",
            f"--name={self._POOLNAME}",
            "URL",
            "--thumbprint",
            "fake thumbprint",
        ]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_bind_when_unencrypted_tang_trust(self):
        """
        Binding when unencrypted and trusting URL should return an error.
        """
        command_line = self._MENU + [
            "nbde",
            f"--name={self._POOLNAME}",
            "URL",
            "--trust-url",
        ]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_bind_when_unencrypted_tpm(self):
        """
        Binding when unencrypted with tpm should return an error.
        """
        command_line = self._MENU + [
            "tpm2",
            f"--name={self._POOLNAME}",
        ]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_bind_when_unencrypted_keyring(self):
        """
        Binding when unencrypted with keyring should return an error.
        """
        command_line = self._MENU + ["keyring", f"--name={self._POOLNAME}", "keydesc"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)


class BindTestCase2(SimTestCase):
    """
    Test binding when pool is encrypted.
    """

    _MENU = ["--propagate", "pool", "encryption", "bind"]
    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        with RandomKeyTmpFile() as fname:
            command_line = [
                "--propagate",
                "key",
                "set",
                "--keyfile-path",
                fname,
                self._KEY_DESC,
            ]
            RUNNER(command_line)

        command_line = [
            "--propagate",
            "pool",
            "create",
            "--key-desc",
            self._KEY_DESC,
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_bind_when_bound_1(self):
        """
        Binding when encrypted and bound with Clevis should not raise a no
        change error when token slot is not specified.
        """
        command_line = self._MENU + [
            "tpm2",
            f"--name={self._POOLNAME}",
        ]
        RUNNER(command_line)
        TEST_RUNNER(command_line)

    def test_bind_when_bound_2(self):
        """
        Binding when encrypted already should raise a no change error.
        """
        command_line = self._MENU + [
            "keyring",
            f"--name={self._POOLNAME}",
            self._KEY_DESC,
        ]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)


class BindTestCase3(SimTestCase):
    """
    Test binding when pool is encrypted.
    """

    _MENU = ["--propagate", "pool", "encryption", "bind"]
    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        with RandomKeyTmpFile() as fname:
            command_line = [
                "--propagate",
                "key",
                "set",
                "--keyfile-path",
                fname,
                self._KEY_DESC,
            ]
            RUNNER(command_line)

        command_line = [
            "--propagate",
            "pool",
            "create",
            "--clevis=tpm2",
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_bind_when_bound(self):
        """
        Binding with keyring when already bound with clevis should succeed.
        """
        command_line = self._MENU + [
            "keyring",
            f"--name={self._POOLNAME}",
            self._KEY_DESC,
        ]
        TEST_RUNNER(command_line)


class RebindTestCase(SimTestCase):
    """
    Test 'rebind' on a sim pool when the pool is unencrypted.
    """

    _MENU = ["--propagate", "pool", "encryption", "rebind"]
    _POOLNAME = "poolname"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_rebind_with_clevis(self):
        """
        Rebinding with Clevis when unencrypted should return an error.
        """
        command_line = self._MENU + ["clevis", f"--name={self._POOLNAME}"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_rebind_with_key(self):
        """
        Rebinding with kernel keyring when unencrypted should return an error.
        """
        command_line = self._MENU + ["keyring", f"--name={self._POOLNAME}", "keydesc"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)


class RebindTestCase2(SimTestCase):
    """
    Rebind when pool is already encrypted using a key in the kernel keyring.
    """

    _MENU = ["--propagate", "pool", "encryption", "rebind"]
    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        with RandomKeyTmpFile() as fname:
            command_line = [
                "--propagate",
                "key",
                "set",
                "--keyfile-path",
                fname,
                self._KEY_DESC,
            ]
            RUNNER(command_line)

        command_line = [
            "--propagate",
            "pool",
            "create",
            "--key-desc",
            self._KEY_DESC,
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_rebind_with_clevis(self):
        """
        Rebinding with Clevis when encrypted with key should return an error.
        """
        command_line = self._MENU + ["clevis", f"--name={self._POOLNAME}"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_rebind_keyring(self):
        """
        Rebinding with kernel keyring with same key should return an error.
        """
        command_line = self._MENU + [
            "keyring",
            f"--name={self._POOLNAME}",
            self._KEY_DESC,
        ]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)

    def test_rebind_keyring_new_key_description(self):
        """
        Rebinding with different kernel key description succeeds.
        """
        new_key_desc = "new_key_desc"
        with RandomKeyTmpFile() as fname:
            command_line = [
                "--propagate",
                "key",
                "set",
                "--keyfile-path",
                fname,
                new_key_desc,
            ]
            RUNNER(command_line)
        command_line = self._MENU + [
            "keyring",
            f"--name={self._POOLNAME}",
            new_key_desc,
        ]
        TEST_RUNNER(command_line)


class RebindTestCase3(SimTestCase):
    """
    Rebind when pool is already encrypted using tang.
    """

    _MENU = ["--propagate", "pool", "encryption", "rebind"]
    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        command_line = [
            "--propagate",
            "pool",
            "create",
            self._POOLNAME,
            "--clevis=tang",
            "--trust-url",
            "--tang-url=http",
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_rebind_with_clevis(self):
        """
        Rebinding with Clevis should succeed.
        """
        command_line = self._MENU + ["clevis", f"--name={self._POOLNAME}"]
        TEST_RUNNER(command_line)

    def test_rebind_keyring(self):
        """
        Rebinding with kernel keyring should return an error.
        """
        command_line = self._MENU + [
            "keyring",
            f"--name={self._POOLNAME}",
            self._KEY_DESC,
        ]
        self.check_error(StratisCliEngineError, command_line, _ERROR)


class UnbindTestCase(SimTestCase):
    """
    Test 'unbind' on a sim pool.
    """

    _MENU = ["--propagate", "pool", "encryption", "unbind"]
    _POOLNAME = "poolname"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_unbind_when_unencrypted(self):
        """
        Unbinding when unencrypted should return an error.
        """
        command_line = self._MENU + ["clevis", f"--name={self._POOLNAME}"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)


class UnbindTestCase2(SimTestCase):
    """
    Test unbinding when pool is encrypted.
    """

    _MENU = ["--propagate", "pool", "encryption", "unbind"]
    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        with RandomKeyTmpFile() as fname:
            command_line = [
                "--propagate",
                "key",
                "set",
                "--keyfile-path",
                fname,
                self._KEY_DESC,
            ]
            RUNNER(command_line)

        command_line = [
            "--propagate",
            "pool",
            "create",
            "--key-desc",
            self._KEY_DESC,
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_unbind_when_unbound(self):
        """
        Unbinding when encrypted but with only one binding mechanism results in
        an engine error, as removing the one remaining binding mechanism would
        make the pool unreadable as soon as it is stopped.
        """
        command_line = self._MENU + ["clevis", f"--name={self._POOLNAME}"]
        self.check_error(StratisCliEngineError, command_line, _ERROR)

    def test_unbind_when_bound(self):
        """
        Bind and then unbind the pool. Unbinding should succeed.
        """
        command_line = [
            "--propagate",
            "pool",
            "encryption",
            "bind",
            "nbde",
            f"--name={self._POOLNAME}",
            "URL",
            "--trust-url",
        ]
        RUNNER(command_line)
        command_line = self._MENU + ["clevis", f"--name={self._POOLNAME}"]
        TEST_RUNNER(command_line)

    def test_unbind_with_unused_token_slot(self):
        """
        Unbind with unused token slot.
        """
        command_line = [
            "--propagate",
            "pool",
            "encryption",
            "bind",
            "nbde",
            f"--name={self._POOLNAME}",
            "URL",
            "--trust-url",
        ]
        RUNNER(command_line)
        command_line = self._MENU + [
            "clevis",
            f"--name={self._POOLNAME}",
            "--token-slot=32",
        ]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)


class OffTestCase(SimTestCase):
    """
    Test turning encryption off when pool is encrypted.
    """

    _MENU = ["--propagate", "pool", "encryption", "off", "--in-place"]
    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        with RandomKeyTmpFile() as fname:
            command_line = [
                "--propagate",
                "key",
                "set",
                "--keyfile-path",
                fname,
                self._KEY_DESC,
            ]
            RUNNER(command_line)

        command_line = [
            "--propagate",
            "pool",
            "create",
            "--key-desc",
            self._KEY_DESC,
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_decrypt_with_name(self):
        """
        Decrypt an encrypted pool, specifying the pool by name.
        """
        command_line = self._MENU + [
            f"--name={self._POOLNAME}",
        ]
        RUNNER(command_line)


class OffTestCase2(SimTestCase):
    """
    Test turning encryption off when pool is not encrypted.
    """

    _MENU = ["--propagate", "pool", "encryption", "off", "--in-place"]
    _POOLNAME = "poolname"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_decrypt_with_name(self):
        """
        Decrypting when unencrypted should return an error.
        """
        command_line = self._MENU + [
            f"--name={self._POOLNAME}",
        ]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)


class ReencryptTestCase(SimTestCase):
    """
    Test re-encrypting when pool is encrypted.
    """

    _MENU = ["--propagate", "pool", "encryption", "reencrypt", "--in-place"]
    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        with RandomKeyTmpFile() as fname:
            command_line = [
                "--propagate",
                "key",
                "set",
                "--keyfile-path",
                fname,
                self._KEY_DESC,
            ]
            RUNNER(command_line)

        command_line = [
            "--propagate",
            "pool",
            "create",
            "--key-desc",
            self._KEY_DESC,
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_reencrypt_with_name(self):
        """
        Re-encrypt an encrypted pool, specifying the pool by name.
        """
        command_line = self._MENU + [
            f"--name={self._POOLNAME}",
        ]
        RUNNER(command_line)


class ReencryptTestCase2(SimTestCase):
    """
    Test reencryption when pool is not encrypted.
    """

    _MENU = ["--propagate", "pool", "encryption", "reencrypt", "--in-place"]
    _POOLNAME = "poolname"

    def setUp(self):
        super().setUp()
        command_line = ["pool", "create", self._POOLNAME] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_reencrypt_with_name(self):
        """
        Reencrypting when unencrypted should return an error.
        """
        command_line = self._MENU + [
            f"--name={self._POOLNAME}",
        ]
        self.check_error(StratisCliEngineError, command_line, _ERROR)


class EncryptTestCase(SimTestCase):
    """
    Test encrypting when pool is already encrypted.
    """

    _MENU = ["--propagate", "pool", "encryption", "on", "--in-place"]
    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        with RandomKeyTmpFile() as fname:
            command_line = [
                "--propagate",
                "key",
                "set",
                "--keyfile-path",
                fname,
                self._KEY_DESC,
            ]
            RUNNER(command_line)

        command_line = [
            "--propagate",
            "pool",
            "create",
            "--key-desc",
            self._KEY_DESC,
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_encrypt_with_name(self):
        """
        Encrypting when already encrypted should return an error.
        """
        command_line = self._MENU + [
            f"--name={self._POOLNAME}",
            "--clevis=tpm2",
        ]
        self.check_error(StratisCliNoChangeError, command_line, _ERROR)


class EncryptTestCase2(SimTestCase):
    """
    Test encrypting when pool is not already encrypted.
    """

    _MENU = ["--propagate", "pool", "encryption", "on", "--in-place"]
    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        command_line = [
            "--propagate",
            "pool",
            "create",
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_encrypt_with_name(self):
        """
        Encrypting when not already encrypted should succeed.
        """
        command_line = self._MENU + [
            f"--name={self._POOLNAME}",
            "--clevis=tpm2",
        ]
        TEST_RUNNER(command_line)

    def test_encryption_with_no_encryption_params(self):
        """
        Encrypting without any encryption method fully specified should fail.
        """
        command_line = self._MENU + [
            f"--name={self._POOLNAME}",
        ]
        self.check_error(StratisCliEngineError, command_line, _ERROR)


class NoInPlaceTestCase(SimTestCase):
    """
    Test encrypting when pool is not already encrypted.
    """

    _POOLNAME = "poolname"
    _KEY_DESC = "keydesc"

    def setUp(self):
        super().setUp()
        command_line = [
            "--propagate",
            "pool",
            "create",
            self._POOLNAME,
        ] + _DEVICE_STRATEGY()
        RUNNER(command_line)

    def test_on(self):
        """
        In place must be specified for on.
        """
        command_line = [
            "--propagate",
            "pool",
            "encryption",
            "on",
            f"--name={self._POOLNAME}",
            "--clevis=tpm2",
        ]
        self.check_error(StratisCliInPlaceNotSpecified, command_line, _ERROR)

    def test_off(self):
        """
        In place must be specified for off.
        """
        command_line = [
            "--propagate",
            "pool",
            "encryption",
            "off",
            f"--name={self._POOLNAME}",
        ]
        self.check_error(StratisCliInPlaceNotSpecified, command_line, _ERROR)

    def test_reencrypt(self):
        """
        In place must be specified for reencrypt.
        """
        command_line = [
            "--propagate",
            "pool",
            "encryption",
            "reencrypt",
            f"--name={self._POOLNAME}",
        ]
        self.check_error(StratisCliInPlaceNotSpecified, command_line, _ERROR)
