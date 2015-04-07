#!/usr/bin/env python
# Copyright (C) 2013 Yahoo! Inc.
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

import sys

from neutronclient.common import exceptions
from neutronclient.neutron.v2_0 import quota as test_quota
from neutronclient.tests.unit import test_cli20


class CLITestV20Quota(test_cli20.CLITestV20Base):
    def test_show_quota(self):
        resource = 'quota'
        cmd = test_quota.ShowQuota(
            test_cli20.MyApp(sys.stdout), None)
        args = ['--tenant-id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args)

    def test_update_quota(self):
        resource = 'quota'
        cmd = test_quota.UpdateQuota(
            test_cli20.MyApp(sys.stdout), None)
        args = ['--tenant-id', self.test_id, '--network', 'test']
        self.assertRaises(
            exceptions.NeutronClientException, self._test_update_resource,
            resource, cmd, self.test_id, args=args,
            extrafields={'network': 'new'})

    def test_delete_quota_get_parser(self):
        cmd = test_cli20.MyApp(sys.stdout)
        test_quota.DeleteQuota(cmd, None).get_parser(cmd)
