/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:Organizations
 * @description This form is for adding/editing an organization
*/

export default
    angular.module('OrganizationFormDefinition', [])
        .value('OrganizationForm', {

            addTitle: 'New Organization', //Title in add mode
            editTitle: '{{ name }}', //Title in edit mode
            name: 'organization', //entity or model name in singular form
            tabs: true,

            fields: {
                name: {
                    label: 'Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: false
                },
                description: {
                    label: 'Description',
                    type: 'text',
                    addRequired: false,
                    editRequired: false
                }
            },

            buttons: { //for now always generates <button> tags
                save: {
                    ngClick: 'formSave()', //$scope.function to call on click, optional
                    ngDisabled: true //Disable when $pristine or $invalid, optional
                },
                cancel: {
                    ngClick: 'formCancel()'
                }
            },

            related: {

                users: {
                    type: 'collection',
                    title: 'Users',
                    iterator: 'user',
                    index: false,
                    open: false,

                    actions: {
                        add: {
                            ngClick: "add('users')",
                            label: 'Add',
                            awToolTip: 'Add a new user',
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ADD'
                        }
                    },

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

                    fieldActions: {
                        edit: {
                            label: 'Edit',
                            ngClick: "edit('users', user.id, user.username)",
                            icon: 'icon-edit',
                            'class': 'btn-default',
                            awToolTip: 'Edit user'
                        },
                        "delete": {
                            label: 'Delete',
                            ngClick: "delete('users', user.id, user.username, 'users')",
                            icon: 'icon-trash',
                            "class": 'btn-danger',
                            awToolTip: 'Remove user'
                        }
                    }
                },

                admins: { // Assumes a plural name (e.g. things)
                    type: 'collection',
                    title: 'Administrators',
                    iterator: 'admin', // Singular form of name (e.g.  thing)
                    index: false,
                    open: false, // Open accordion on load?
                    base: '/users',
                    actions: { // Actions displayed top right of list
                        add: {
                            ngClick: "add('admins')",
                            label: 'Add',
                            awToolTip: 'Add new administrator',
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ADD'
                        }
                    },
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
                    fieldActions: { // Actions available on each row
                        edit: {
                            label: 'Edit',
                            ngClick: "edit('users', admin.id, admin.username)",
                            icon: 'icon-edit',
                            awToolTip: 'Edit administrator',
                            'class': 'btn-default'
                        },
                        "delete": {
                            label: 'Delete',
                            ngClick: "delete('admins', admin.id, admin.username, 'administrators')",
                            icon: 'icon-trash',
                            "class": 'btn-danger',
                            awToolTip: 'Remove administrator'
                        }
                    }
                }

            }

        }); //OrganizationForm
