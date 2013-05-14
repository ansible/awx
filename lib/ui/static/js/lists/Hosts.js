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
        selectInstructions: 'Check the Select checkbox next to each host to be added, and click Finished when done. Use the green <i class=\"icon-plus\"></i> button to create a new host.', 
        editTitle: 'Hosts',
        
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
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addHost()',
                class: 'btn btn-mini btn-success',
                awToolTip: 'Create a new host'
                }
            },

        fieldActions: {
            edit: {
                ngClick: "editHost(\{\{ host.id \}\})",
                icon: 'icon-edit',
                awToolTip: 'Edit host'
                },

            delete: {
                ngClick: "deleteHost(\{\{ host.id \}\},'\{\{ host.name \}\}')",
                icon: 'icon-remove',
                class: 'btn-danger',
                awToolTip: 'Delete host'
                }
            }
        });
