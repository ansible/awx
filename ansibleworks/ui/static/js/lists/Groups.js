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
        selectInstructions: 'Click on a row to select it, and click Finished when done. Use the green <i class=\"icon-plus\"></i> button to create a new row.', 
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
                label: 'Add',
                icon: 'icon-plus',
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addGroup()',
                class: 'btn-success btn-small',
                awToolTip: 'Create a new group'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editGroup(\{\{ group.id \}\})",
                icon: 'icon-edit',
                class: 'btn-small',
                awToolTip: 'View/Edit group'
                },

            delete: {
                label: 'Delete',
                ngClick: "deleteGroup(\{\{ group.id \}\},'\{\{ group.name \}\}')",
                icon: 'icon-remove',
                class: 'btn-small btn-danger',
                awToolTip: 'Delete group'
                }
            }
        });