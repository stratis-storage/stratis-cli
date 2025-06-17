# Copyright 2016 Red Hat, Inc.
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
General constants.
"""
# isort: THIRDPARTY
from packaging.version import Version

SERVICE = "org.storage.stratis3"
TOP_OBJECT = "/org/storage/stratis3"

SECTOR_SIZE = 512

MAXIMUM_STRATISD_VERSION = "4.0.0"
MINIMUM_STRATISD_VERSION = "3.8.2"
assert Version(MINIMUM_STRATISD_VERSION) < Version(MAXIMUM_STRATISD_VERSION)

REVISION = f"r{MINIMUM_STRATISD_VERSION.split('.')[1]}"

BLOCKDEV_INTERFACE = f"org.storage.stratis3.blockdev.{REVISION}"
FILESYSTEM_INTERFACE = f"org.storage.stratis3.filesystem.{REVISION}"
MANAGER_INTERFACE = f"org.storage.stratis3.Manager.{REVISION}"
POOL_INTERFACE = f"org.storage.stratis3.pool.{REVISION}"
REPORT_INTERFACE = f"org.storage.stratis3.Report.{REVISION}"
