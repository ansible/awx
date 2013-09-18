/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Groups.js 
 *  List view object for Group data model.
 *
 *  
 */
angular.module('GroupListDefinition', [])
    .value(
    'GroupList', {
        
        name: 'groups',
        iterator: 'group',
        selectTitle: 'Copy Groups',
        editTitle: 'Groups',
        index: true,
        well: false,
        
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
             help: {
                awPopOver: "Choose groups by clicking on each group you wish to add. Click the <em>Select</em> button to add the groups to " +
                    "the selected inventory group.",
                dataPlacement: 'left',
                dataContainer: '#form-modal .modal-content',
                icon: "icon-question-sign",
                mode: 'all',
                'class': 'btn-xs btn-info btn-help pull-right',
                awToolTip: 'Click for help',
                dataTitle: 'Adding Groups',
                iconSize: 'large'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editGroup(\{\{ group.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-xs btn-default',
                awToolTip: 'View/Edit group'
                },

            "delete": {
                label: 'Delete',
                ngClick: "deleteGroup(\{\{ group.id \}\},'\{\{ group.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-xs btn-danger',
                awToolTip: 'Delete group'
                }
            }
        });