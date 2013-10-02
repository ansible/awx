/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  InventorySummary.js 
 *
 *  Summary of groups contained within an inventory
 * 
 */
angular.module('InventorySummaryDefinition', [])
    .value(
    'InventorySummary', {

        name: 'groups',
        iterator: 'group',
        editTitle: 'Inventory Summary',
        index: false,
        hover: true,
        
        fields: {
            name: {
                key: true,
                label: 'Name'
                },
            failures: {
                label: 'Hosts Failures'
                },
            source: {
                label: 'Source'
                },
            last_update: {
                label: 'Last Update'
                },
            status: {
                label: 'Update Status'
                }
            },

         actions: {
            },

        fieldActions: {
            }
    });
            