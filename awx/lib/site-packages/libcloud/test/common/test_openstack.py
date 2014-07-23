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

from mock import Mock

from libcloud.common.openstack import OpenStackBaseConnection
from libcloud.utils.py3 import PY25


class OpenStackBaseConnectionTest(unittest.TestCase):

    def setUp(self):
        self.timeout = 10
        OpenStackBaseConnection.conn_classes = (None, Mock())
        self.connection = OpenStackBaseConnection('foo', 'bar',
                                                  timeout=self.timeout,
                                                  ex_force_auth_url='https://127.0.0.1')
        self.connection.driver = Mock()
        self.connection.driver.name = 'OpenStackDriver'

    def test_base_connection_timeout(self):
        self.connection.connect()
        self.assertEqual(self.connection.timeout, self.timeout)
        if PY25:
            self.connection.conn_classes[1].assert_called_with(host='127.0.0.1',
                                                               port=443)
        else:
            self.connection.conn_classes[1].assert_called_with(host='127.0.0.1',
                                                               port=443,
                                                               timeout=10)


if __name__ == '__main__':
    sys.exit(unittest.main())
