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
        selectTitle: 'Add Group',
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
            add: {
                label: 'Create New Group',
                icon: 'icon-plus',
                mode: 'all',             // One of: edit, select, all
                ngClick: 'createGroup()',
                "class": 'btn-success btn-mini',
                awToolTip: 'Create a new group'
                },
             help: {
                awPopOver: "Select groups by clicking on each group you wish to add. Add the selected groups to your inventory " +
                    "or to the selected parent group by clicking the <em>Select</em> button. You can also create a new group by clicking the " +
                    "<em>Create New Group</em> button.",
                dataPlacement: 'left',
                dataContainer: '#form-modal .modal-content',
                icon: "icon-question-sign",
                mode: 'all',
                'class': 'btn-mini btn-info btn-help',
                awToolTip: 'Click for help',
                dataTitle: 'Adding Groups',
                id: 'group-help-button',
                iconSize: 'large'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editGroup(\{\{ group.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-mini btn-default',
                awToolTip: 'View/Edit group'
                },

            "delete": {
                label: 'Delete',
                ngClick: "deleteGroup(\{\{ group.id \}\},'\{\{ group.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-mini btn-danger',
                awToolTip: 'Delete group'
                }
            }
        });