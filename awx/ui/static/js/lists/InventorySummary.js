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
        editTitle: 'Inventory Summary: {{ inventory_name }}',
        showTitle: true,
        well: false,
        index: false,
        hover: true,
        
        fields: {
            name: {
                key: true,
                label: 'Group',
                noLink: true,
                badges: [
                    { //Active Failures
                      icon: "\{\{ 'icon-failures-' + group.has_active_failures \}\}",
                      toolTip: 'Indicates if inventory contains hosts with active failures',
                      toolTipPlacement: 'bottom'
                      },
                    { //Cloud Status
                      icon: "\{\{ 'icon-cloud-' + group.status \}\}",
                      toolTip: 'Indicates if inventory contains hosts with active failures',
                      toolTipPlacement: 'bottom'
                      }]
                },
            failures: {
                label: 'Active<br />Failures'
                },
            source: {
                label: 'Source'
                },
            last_update: {
                label: 'Last<br />Updated'
                },
            status: {
                label: 'Update<br />Status'
                }
            },

         actions: {
            },

        fieldActions: {
            }
    });
            