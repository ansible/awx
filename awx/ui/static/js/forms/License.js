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

    }); //form

    