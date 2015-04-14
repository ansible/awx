# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import testtools

from troveclient.v1 import limits


class LimitsTest(testtools.TestCase):
    """This class tests the calling code for the Limits API."""

    def setUp(self):
        super(LimitsTest, self).setUp()
        self.limits = limits.Limits(mock.Mock())
        self.limits.api.client = mock.Mock()

    def tearDown(self):
        super(LimitsTest, self).tearDown()

    def test_list(self):
        resp = mock.Mock()
        resp.status_code = 200
        body = {"limits":
                [
                    {'maxTotalInstances': 55,
                     'verb': 'ABSOLUTE',
                     'maxTotalVolumes': 100},
                    {'regex': '.*',
                     'nextAvailable': '2011-07-21T18:17:06Z',
                     'uri': '*',
                     'value': 10,
                     'verb': 'POST',
                     'remaining': 2, 'unit': 'MINUTE'},
                    {'regex': '.*',
                     'nextAvailable': '2011-07-21T18:17:06Z',
                     'uri': '*',
                     'value': 10,
                     'verb': 'PUT',
                     'remaining': 2,
                     'unit': 'MINUTE'},
                    {'regex': '.*',
                     'nextAvailable': '2011-07-21T18:17:06Z',
                     'uri': '*',
                     'value': 10,
                     'verb': 'DELETE',
                     'remaining': 2,
                     'unit': 'MINUTE'},
                    {'regex': '.*',
                     'nextAvailable': '2011-07-21T18:17:06Z',
                     'uri': '*',
                     'value': 10,
                     'verb': 'GET',
                     'remaining': 2, 'unit': 'MINUTE'}]}
        response = (resp, body)

        mock_get = mock.Mock(return_value=response)
        self.limits.api.client.get = mock_get
        self.assertIsNotNone(self.limits.list())
        mock_get.assert_called_once_with("/limits")

    def test_list_errors(self):
        status_list = [400, 401, 403, 404, 408, 409, 413, 500, 501]
        for status_code in status_list:
            self._check_error_response(status_code)

    def _check_error_response(self, status_code):
        RESPONSE_KEY = "limits"

        resp = mock.Mock()
        resp.status_code = status_code
        body = {RESPONSE_KEY: {
            'absolute': {},
            'rate': [
                {'limit': []}]}}
        response = (resp, body)

        mock_get = mock.Mock(return_value=response)
        self.limits.api.client.get = mock_get
        self.assertRaises(Exception, self.limits.list)
