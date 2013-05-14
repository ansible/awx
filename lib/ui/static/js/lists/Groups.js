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
        selectInstructions: 'Check the Select checkbox next to each group to be added, and click Finished when done. Use the green <i class=\"icon-plus\"></i> button to create a new group.', 
        
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
                ngClick: 'addGroup()',
                class: 'btn btn-mini btn-success',
                awToolTip: 'Create a new group'
                }
            },

        fieldActions: {
            edit: {
                ngClick: "editGroup(\{\{ group.id \}\})",
                icon: 'icon-edit',
                awToolTip: 'Edit group'
                },

            delete: {
                ngClick: "deleteGroup(\{\{ group.id \}\},'\{\{ group.name \}\}')",
                icon: 'icon-remove',
                class: 'btn-danger',
                awToolTip: 'Delete group'
                }
            }
        });