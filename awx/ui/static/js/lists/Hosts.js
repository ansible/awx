/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
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
        selectTitle: 'Add Existing Hosts',
        editTitle: 'Hosts',
        index: true,
        well: false,

        fields: {
            name: {
                key: true,
                label: 'Host Name',
                linkTo: "/inventories/\{\{ inventory_id \}\}/hosts/\{\{ host.id \}\}"
                },
            description: {
                label: 'Description'
                }
            },
        
        actions: {
            help: {
                awPopOver: "Select hosts by clicking on each host you wish to add. Add the selected hosts to the group by clicking the <em>Select</em> button.",
                dataContainer: '#form-modal .modal-content',
                mode: 'all',
                awToolTip: 'Click for help',
                dataTitle: 'Selecting Hosts'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editHost(\{\{ host.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-xs',
                awToolTip: 'View/Edit host',
                dataPlacement: 'top'
                },

            "delete": {
                label: 'Delete',
                ngClick: "deleteHost(\{\{ host.id \}\},'\{\{ host.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-xs',
                awToolTip: 'Delete host',
                dataPlacement: 'top'
                }
            }
        });
