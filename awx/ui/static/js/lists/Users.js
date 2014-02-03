/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
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
        selectInstructions: '<p>Select existing users by clicking each user or checking the related checkbox. When finished, click the blue ' +
            '<em>Select</em> button, located bottom right.</p> <p>When available, a brand new user can be created by clicking the green ' +
            '<em>Create New</em> button.</p>', 
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
                label: 'Create New',
                mode: 'all',                      // One of: edit, select, all
                ngClick: 'addUser()',
                basePaths: ['organizations','users'],        // base path must be in list, or action not available
                "class": 'btn-xs',
                awToolTip: 'Create a new user'
                },
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                mode: 'all'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editUser(\{\{ user.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-xs btn-default',
                awToolTip: 'Edit user',
                dataPlacement: 'top'
                },

            "delete": {
                label: 'Delete',
                ngClick: "deleteUser(\{\{ user.id \}\},'\{\{ user.username \}\}')",
                icon: 'icon-trash',
                "class": 'btn-xs btn-danger',
                awToolTip: 'Delete user',
                dataPlacement: 'top'
                }
            }
        });
