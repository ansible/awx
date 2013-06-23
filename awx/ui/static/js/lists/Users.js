/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Users.js 
 *  List view object for Users data model.
 *
 * 
 */
angular.module('UserListDefinition', [])
    .value(
    'UserList', {
        
        name: 'users',
        iterator: 'user',
        selectTitle: 'Add Users',
        editTitle: 'Users',
        selectInstructions: 'Check the Select checkbox next to each user to be added, and click Finished when done. Use the green <i class=\"icon-plus\"></i> button to create a new user.', 
        index: true,
        hover: true, 
        
        fields: {
            username: {
                key: true,
                label: 'Username'
                },
            first_name: {
                label: 'First Name'
                },
            last_name: {
                label: 'Last Name'
                }
            },
        
        actions: {
            add: {
                label: 'Add',
                icon: 'icon-plus',
                mode: 'all',                      // One of: edit, select, all
                ngClick: 'addUser()',
                basePaths: ['organizations','users'],        // base path must be in list, or action not available
                "class": 'btn-success btn-small',
                awToolTip: 'Create a new user'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editUser(\{\{ user.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-small btn-success',
                awToolTip: 'View/Edit user'
                },

            "delete": {
                label: 'Delete',
                ngClick: "deleteUser(\{\{ user.id \}\},'\{\{ user.username \}\}')",
                icon: 'icon-remove',
                "class": 'btn-small btn-danger',
                awToolTip: 'Delete user'
                }
            }
        });
