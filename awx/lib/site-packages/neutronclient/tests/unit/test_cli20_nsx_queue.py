#!/usr/bin/env python
# Copyright 2013 VMware Inc.
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

from neutronclient.neutron.v2_0.nsx import qos_queue as qos
from neutronclient.tests.unit import test_cli20


class CLITestV20QosQueueJSON(test_cli20.CLITestV20Base):
    def setUp(self):
        super(CLITestV20QosQueueJSON, self).setUp(
            plurals={'qos_queues': 'qos_queue'})

    def test_create_qos_queue(self):
        """Create a qos queue."""
        resource = 'qos_queue'
        cmd = qos.CreateQoSQueue(
            test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        name = 'my_queue'
        default = False
        args = ['--default', default, name]
        position_names = ['name', 'default']
        position_values = [name, default]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_create_qos_queue_all_values(self):
        """Create a qos queue."""
        resource = 'qos_queue'
        cmd = qos.CreateQoSQueue(
            test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        name = 'my_queue'
        default = False
        min = '10'
        max = '40'
        qos_marking = 'untrusted'
        dscp = '0'
        args = ['--default', default, '--min', min, '--max', max,
                '--qos-marking', qos_marking, '--dscp', dscp, name]
        position_names = ['name', 'default', 'min', 'max', 'qos_marking',
                          'dscp']
        position_values = [name, default, min, max, qos_marking, dscp]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_list_qos_queue(self):
        resources = "qos_queues"
        cmd = qos.ListQoSQueue(
            test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_show_qos_queue_id(self):
        resource = 'qos_queue'
        cmd = qos.ShowQoSQueue(
            test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id,
                                 args, ['id'])

    def test_delete_qos_queue(self):
        resource = 'qos_queue'
        cmd = qos.DeleteQoSQueue(
            test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(resource, cmd, myid, args)


class CLITestV20QosQueueXML(CLITestV20QosQueueJSON):
    format = 'xml'
