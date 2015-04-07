# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Sylvain Afchain <sylvain.afchain@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys

from neutronclient.neutron.v2_0 import metering
from neutronclient.tests.unit import test_cli20


class CLITestV20MeteringJSON(test_cli20.CLITestV20Base):
    def test_create_metering_label(self):
        """Create a metering label."""
        resource = 'metering_label'
        cmd = metering.CreateMeteringLabel(
            test_cli20.MyApp(sys.stdout), None)
        name = 'my label'
        myid = 'myid'
        description = 'my description'
        args = [name, '--description', description, '--shared']
        position_names = ['name', 'description', 'shared']
        position_values = [name, description, True]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_list_metering_labels(self):
        resources = "metering_labels"
        cmd = metering.ListMeteringLabel(
            test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd)

    def test_delete_metering_label(self):
        """Delete a metering label."""
        resource = 'metering_label'
        cmd = metering.DeleteMeteringLabel(
            test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(resource, cmd, myid, args)

    def test_show_metering_label(self):
        resource = 'metering_label'
        cmd = metering.ShowMeteringLabel(
            test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id'])

    def test_create_metering_label_rule(self):
        resource = 'metering_label_rule'
        cmd = metering.CreateMeteringLabelRule(
            test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        metering_label_id = 'aaa'
        remote_ip_prefix = '10.0.0.0/24'
        direction = 'ingress'
        args = [metering_label_id, remote_ip_prefix, '--direction', direction,
                '--excluded']
        position_names = ['metering_label_id', 'remote_ip_prefix', 'direction',
                          'excluded']
        position_values = [metering_label_id, remote_ip_prefix,
                           direction, True]
        self._test_create_resource(resource, cmd, metering_label_id,
                                   myid, args, position_names, position_values)

    def test_list_metering_label_rules(self):
        resources = "metering_label_rules"
        cmd = metering.ListMeteringLabelRule(
            test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd)

    def test_delete_metering_label_rule(self):
        resource = 'metering_label_rule'
        cmd = metering.DeleteMeteringLabelRule(
            test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(resource, cmd, myid, args)

    def test_show_metering_label_rule(self):
        resource = 'metering_label_rule'
        cmd = metering.ShowMeteringLabelRule(
            test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id'])


class CLITestV20MeteringXML(CLITestV20MeteringJSON):
    format = 'xml'
