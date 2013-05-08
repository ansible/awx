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
        editInstructions: 'Create new users from the Organizations tab. Each Organizaton has an associated list of Users.',
        
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
                icon: 'icon-plus',
                mode: 'select',             // One of: edit, select, all
                ngClick: 'addUser()',
                class: 'btn btn-mini btn-success',
                awToolTip: 'Create a new row'
                }
            },

        fieldActions: {
            edit: {
                ngClick: "editUser(\{\{ user.id \}\})",
                icon: 'icon-edit',
                awToolTip: 'Edit'
                },

            delete: {
                ngClick: "deleteUser(\{\{ user.id \}\},'\{\{ user.username \}\}')",
                icon: 'icon-remove',
                class: 'btn-danger',
                awToolTip: 'Delete'
                }
            }
        });
