/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  LicenseForm.js
 *
 *
 */

'use strict';

angular.module('LicenseFormDefinition', [])
    .value('LicenseForm', {

        name: 'license',
        well: false,

        tabs: [{
            name: 'license',
            label: 'License'
        }, {
            name: 'managed',
            label: 'Managed Hosts'
        }],

        fields: {
            license_status: {
                type: 'custom',
                control: "<div class=\"license-status\" ng-class=\"status_color\"><i class=\"fa fa-circle\"></i> " +
                    "{{ license_status }}</span></div>",
                readonly: true,
                tab: 'license'
            },
            license_key: {
                label: 'Key',
                type: 'textarea',
                'class': 'modal-input-xlarge',
                readonly: true,
                tab: 'license'
            },
            license_date: {
                label: 'Expires On',
                type: 'text',
                readonly: true,
                tab: 'license'
            },
            time_remaining: {
                label: 'Time Left',
                type: 'text',
                readonly: true,
                tab: 'license'
            },
            available_instances: {
                label: 'Available',
                type: 'text',
                readonly: true,
                tab: 'managed'
            },
            current_instances: {
                label: 'Used',
                type: 'text',
                readonly: true,
                tab: 'managed'
            },
            free_instances: {
                label: 'Remaining',
                type: 'text',
                readonly: true,
                controlNGClass: 'free_instances_class',
                labelNGClass: 'free_instances_class',
                tab: 'managed'
            }
        }
    });