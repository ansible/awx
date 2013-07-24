/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  License.js
 *  Form definition for LIcense model
 *
 *  
 */
angular.module('LicenseFormDefinition', [])
    .value(
    'LicenseForm', {

        name: 'license',
        well: false,
        well: false,
        forceListeners: true,
        'class': 'horizontal-narrow',                                            

        fields: {
            license_status: {
                label: 'Status',
                type: 'custom',
                control: '<div ng-class=\"status_color\" class=\"license-status\"><i class="icon-circle"></i> \{\{ license_status \}\}</div>',
                readonly: true,
                section: 'License'
                },
            license_key: {
                label: 'Key',
                type: 'textarea',
                section: 'License',
                'class': 'modal-input-xlarge',
                readonly: true
                },
            license_date: {
                label: 'Activated On',
                type: 'text',
                readonly: true,
                section: 'License'
                },
            time_remaining: {
                label: 'Days Left',
                type: 'text',
                readonly: true,
                section: 'License'
                },
            available_instances: {
                label: 'License Count',
                type: 'text',
                readonly: true,
                section: 'Available Servers'
                },
            current_instances: {
                label: 'Used',
                type: 'text',
                readonly: true,
                section: 'Available Servers'
                },
            free_instances: {
                label: 'Remaining',
                type: 'text',
                readonly: true,
                section: 'Available Servers'
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

    }); //form

    