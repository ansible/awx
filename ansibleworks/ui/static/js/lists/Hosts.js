/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Hosts.js 
 *  List view object for Users data model.
 *
 *
 */
angular.module('HostListDefinition', [])
    .value(
    'HostList', {
        
        name: 'hosts',
        iterator: 'host',
        selectTitle: 'Add Host',
        selectInstructions: 'Click on a row to select it, and click Finished when done. Use the green <i class=\"icon-plus\"></i> button to create a new row.', 
        editTitle: 'Hosts',
        index: true,
        
        fields: {
            name: {
                key: true,
                label: 'Name'
                },
            description: {
                label: 'Description'
                }
            },
        
        actions: {
            add: {
                icon: 'icon-plus',
                label: 'Add',
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addHost()',
                class: 'btn-success btn-small',
                awToolTip: 'Create a new host'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editHost(\{\{ host.id \}\})",
                icon: 'icon-edit btn-success',
                class: 'btn-small',
                awToolTip: 'View/Edit host'
                },

            delete: {
                label: 'Delete',
                ngClick: "deleteHost(\{\{ host.id \}\},'\{\{ host.name \}\}')",
                icon: 'icon-remove',
                class: 'btn-small btn-danger',
                awToolTip: 'Delete host'
                }
            }
        });
