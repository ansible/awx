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
        selectTitle: 'Select Host',
        editTitle: 'Hosts',
        index: true,
        well: true,

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
                awPopOver: "Select hosts by clicking on each host you wish to add. Add the selected hosts to the group by clicking the Select button.",
                dataPlacement: 'left',
                dataContainer: "#form-modal",
                icon: "icon-question-sign",
                mode: 'all',
                'class': 'btn-small btn-info',
                awToolTip: 'Click for help',
                dataTitle: 'Selecting Hosts'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editHost(\{\{ host.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-small btn-success',
                awToolTip: 'View/Edit host'
                },

            "delete": {
                label: 'Delete',
                ngClick: "deleteHost(\{\{ host.id \}\},'\{\{ host.name \}\}')",
                icon: 'icon-remove',
                "class": 'btn-small btn-danger',
                awToolTip: 'Delete host'
                }
            }
        });
