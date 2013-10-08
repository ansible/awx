/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  InventoryStatus.js
 *  Form definition for Inventory Status -JSON view
 *
 *  
 */
angular.module('InventoryStatusDefinition', [])
    .value(
    'InventoryStatusForm', {
    
        name: 'inventory_update',
        editTitle: 'Inventory Status', 
        well: false,
        'class': 'horizontal-narrow',

        fields: {
            created: {
                label: 'Created', 
                type: 'text',
                readonly: true
            },
            status: {
                label: 'Status',
                type: 'text',
                readonly: true
            },
            result_stdout: {
                label: 'Std Out', 
                type: 'textarea',
                ngShow: "result_stdout",
                readonly: true,
                rows: 15
            },
            result_traceback: {
                label: 'Traceback', 
                type: 'textarea',
                ngShow: "result_traceback",
                readonly: true,
                rows: 15
            }
        }
    }); //Form