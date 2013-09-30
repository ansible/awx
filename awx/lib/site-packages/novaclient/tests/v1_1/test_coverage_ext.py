# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 IBM Corp.
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

# See: http://wiki.openstack.org/Nova/CoverageExtension for more information
# and usage explanation for this API extension

from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


cs = fakes.FakeClient()


class CoverageTest(utils.TestCase):

    def test_start_coverage(self):
        c = cs.coverage.start()
        cs.assert_called('POST', '/os-coverage/action')

    def test_stop_coverage(self):
        c = cs.coverage.stop()
        return_dict = {'path': '/tmp/tmpdir/report'}
        cs.assert_called_anytime('POST', '/os-coverage/action')

    def test_report_coverage(self):
        c = cs.coverage.report('report')
        return_dict = {'path': '/tmp/tmpdir/report'}
        cs.assert_called_anytime('POST', '/os-coverage/action')

    def test_reset_coverage(self):
        c = cs.coverage.reset()
        cs.assert_called_anytime('POST', '/os-coverage/action')
