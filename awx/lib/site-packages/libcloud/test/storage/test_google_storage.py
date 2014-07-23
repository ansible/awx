# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import unittest

from libcloud.storage.drivers.google_storage import GoogleStorageDriver
from libcloud.test.storage.test_s3 import S3Tests, S3MockHttp

from libcloud.test.file_fixtures import StorageFileFixtures
from libcloud.test.secrets import STORAGE_GOOGLE_STORAGE_PARAMS


class GoogleStorageMockHttp(S3MockHttp):
    fixtures = StorageFileFixtures('google_storage')


class GoogleStorageTests(S3Tests):
    driver_type = GoogleStorageDriver
    driver_args = STORAGE_GOOGLE_STORAGE_PARAMS
    mock_response_klass = GoogleStorageMockHttp

    def test_billing_not_enabled(self):
        # TODO
        pass

    def test_token(self):
        # Not supported on Google Storage
        pass


if __name__ == '__main__':
    sys.exit(unittest.main())
