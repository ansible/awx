/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('UserListDefinition', [])
    .value('UserList', {

        name: 'users',
        iterator: 'user',
        selectTitle: 'Add Users',
        editTitle: 'Users',
        listTitle: 'Users',
        selectInstructions: '<p>Select existing users by clicking each user or checking the related checkbox. When finished, click the blue ' +
            '<em>Select</em> button, located bottom right.</p> <p>When available, a brand new user can be created by clicking the ' +
            '<i class=\"fa fa-plus\"></i> button.</p>',
        index: false,
        hover: true,

        fields: {
            username: {
                key: true,
                label: 'Username',
                columnClass: 'col-md-3 col-sm-3 col-xs-9'
            },
            first_name: {
                label: 'First Name',
                columnClass: 'col-md-3 col-sm-3 hidden-xs'
            },
            last_name: {
                label: 'Last Name',
                columnClass: 'col-md-3 col-sm-3 hidden-xs'
            }
        },

        actions: {
            add: {
                label: 'Create New',
                mode: 'all', // One of: edit, select, all
                ngClick: 'addUser()',
                basePaths: ['organizations', 'users'], // base path must be in list, or action not available
                awToolTip: 'Create a new user',
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD',
                ngShow: 'canAdd'
            }
        },

        fieldActions: {

            columnClass: 'col-md-3 col-sm-3 col-xs-3',

            edit: {
                label: 'Edit',
                ngClick: "editUser(user.id)",
                icon: 'icon-edit',
                "class": 'btn-xs btn-default',
                awToolTip: 'Edit user',
                dataPlacement: 'top',
                ngShow: 'user.summary_fields.user_capabilities.edit'
            },

            view: {
                label: 'View',
                ngClick: "editUser(user.id)",
                "class": 'btn-xs btn-default',
                awToolTip: 'View user',
                dataPlacement: 'top',
                ngShow: '!user.summary_fields.user_capabilities.edit'
            },

            "delete": {
                label: 'Delete',
                ngClick: "deleteUser(user.id, user.username)",
                icon: 'icon-trash',
                "class": 'btn-xs btn-danger',
                awToolTip: 'Delete user',
                dataPlacement: 'top',
                ngShow: 'user.summary_fields.user_capabilities.delete'
            }
        }
    });
