# Copyright 2020 Red Hat, Inc.
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
Key test utilities
"""

# isort: STDLIB
from tempfile import NamedTemporaryFile


class RandomKeyTmpFile:
    """
    Generate a random passphrase and put it in a temporary file.
    """

    # pylint: disable=consider-using-with
    def __init__(self, key_bytes=32):
        """
        Initializer

        :param int key_bytes: the desired length of the key in bytes
        """
        self._tmpfile = NamedTemporaryFile("wb")
        with open("/dev/urandom", "rb") as random:
            random_bytes = random.read(key_bytes)
            self._tmpfile.write(random_bytes)
            self._tmpfile.flush()

    def tmpfile_name(self):
        """
        Get the name of the temporary file.
        """
        return self._tmpfile.name

    def close(self):
        """
        Close and delete the temporary file.
        """
        self._tmpfile.close()

    def __enter__(self):
        """
        For use with the "with" keyword.

        :return str: the path of the file with the random key
        """
        return self._tmpfile.name

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self._tmpfile.close()
        except Exception as error:
            if exc_value is None:
                raise error

            raise error from exc_value
