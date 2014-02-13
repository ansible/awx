/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventoryStatus.js
 *
 *  Use to show inventory sync status
 *  
 */
angular.module('InventoryStatusDefinition', [])
    .value('InventoryStatusForm', {
    
        name: 'inventory_update',
        editTitle: 'Inventory Status',
        well: false,
        'class': 'horizontal-narrow',

        fields: {
            license_error: {
                type: 'alertblock',
                'class': 'alert-info',
                alertTxt: 'The invenvtory update process exceeded the available number of licensed hosts. ' +
                    '<strong><a ng-click=\"viewLicense()\" href=\"\">View your license</a></strong> ' +
                    'for more information.',
                ngShow: 'license_error',
                closeable: true
            },
            created: {
                label: 'Created',
                type: 'text',
                readonly: true
            },
            status: {
                label: 'Status',
                type: 'text',
                readonly: true,
                'class': 'nowrap mono-space resizable',
                rows: '{{ status_rows }}'
            },
            result_stdout: {
                label: 'Std Out',
                type: 'textarea',
                ngShow: 'result_stdout',
                'class': 'nowrap mono-space resizable',
                readonly: true,
                rows: '{{ stdout_rows }}'
            },
            result_traceback: {
                label: 'Traceback',
                type: 'textarea',
                ngShow: 'result_traceback',
                'class': 'nowrap mono-space resizable',
                readonly: true,
                rows: '{{ traceback_rows }}'
            }
        }
    }); //Form