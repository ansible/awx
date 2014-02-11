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
        forceListeners: true,

        fields: {
            license_status: {
                type: 'custom',
                control: "<div class=\"license-status\" ng-class=\"status_color\"><i class=\"fa fa-circle\"></i> " +
                    "{{ license_status }}</span></div>",
                readonly: true,
                section: 'License'
            },
            license_key: {
                label: 'Key',
                type: 'textarea',
                'class': 'modal-input-xlarge',
                readonly: true,
                section: 'License'
            },
            license_date: {
                label: 'Expires On',
                type: 'text',
                readonly: true,
                section: 'License'
            },
            time_remaining: {
                label: 'Time Left',
                type: 'text',
                readonly: true,
                section: 'License'
            },
            available_instances: {
                label: 'Available',
                type: 'text',
                readonly: true,
                section: 'Managed Hosts'
            },
            current_instances: {
                label: 'Used',
                type: 'text',
                readonly: true,
                section: 'Managed Hosts'
            },
            free_instances: {
                label: 'Remaining',
                type: 'text',
                readonly: true,
                section: 'Managed Hosts',
                controlNGClass: 'free_instances_class',
                labelNGClass: 'free_instances_class'
            },
            company_name: {
                label: 'Company',
                type: 'text',
                readonly: true,
                section: 'Contact Info'
            },
            contact_name: {
                label: 'Contact',
                type: 'text',
                readonly: true,
                section: 'Contact Info'
            },
            contact_email: {
                label: 'Contact Email',
                type: 'text',
                readonly: true,
                section: 'Contact Info'
            }
        }
    });