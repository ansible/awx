# -*- coding: utf-8 -*-
#
# Copyright 2014 Red Hat, Inc.
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


# Chassis

CHASSIS_FIELDS = ['uuid', 'description', 'created_at', 'updated_at', 'extra']

CHASSIS_FIELD_LABELS = ['UUID', 'Description', 'Created At', 'Updated At',
                        'Extra']

CHASSIS_LIST_FIELDS = ['uuid', 'description']

CHASSIS_LIST_FIELD_LABELS = ['UUID', 'Description']


# Nodes

NODE_FIELDS = ['chassis_uuid', 'created_at', 'console_enabled', 'driver',
               'driver_info', 'driver_internal_info', 'extra',
               'instance_info', 'instance_uuid', 'last_error',
               'maintenance', 'maintenance_reason', 'power_state',
               'properties', 'provision_state', 'reservation',
               'target_power_state', 'target_provision_state',
               'updated_at', 'inspection_finished_at',
               'inspection_started_at', 'uuid', 'name']

NODE_FIELD_LABELS = ['Chassis UUID', 'Created At', 'Console Enabled', 'Driver',
                     'Driver Info', 'Driver Internal Info', 'Extra',
                     'Instance Info', 'Instance UUID', 'Last Error',
                     'Maintenance', 'Maintenance Reason', 'Power State',
                     'Properties', 'Provision State', 'Reservation',
                     'Target Power State', 'Target Provision State',
                     'Updated At', 'Inspection Finished At',
                     'Inspection Started At', 'UUID', 'Name']

NODE_LIST_FIELDS = ['uuid', 'name', 'instance_uuid', 'power_state',
                    'provision_state', 'maintenance']

NODE_LIST_FIELD_LABELS = ['UUID', 'Name', 'Instance UUID', 'Power State',
                          'Provisioning State', 'Maintenance']


# Ports

PORT_FIELDS = ['uuid', 'address', 'created_at', 'extra', 'node_uuid',
               'updated_at']

PORT_FIELD_LABELS = ['UUID', 'Address', 'Created At', 'Extra', 'Node UUID',
                     'Updated At']

PORT_LIST_FIELDS = ['uuid', 'address']

PORT_LIST_FIELD_LABELS = ['UUID', 'Address']
