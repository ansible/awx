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

            addTitle: 'Create Organization', //Title in add mode
            editTitle: '{{ name }}', //Title in edit mode
            name: 'organization', //entity or model name in singular form
            well: true,
            collapse: true,
            collapseTitle: "Properties",
            collapseMode: 'edit',
            collapseOpen: true,

            actions: {
                stream: {
                    'class': "btn-primary btn-xs activity-btn",
                    ngClick: "showActivity()",
                    awToolTip: "View Activity Stream",
                    awFeature: 'activity_streams',
                    dataPlacement: "top",
                    icon: "icon-comments-alt",
                    mode: 'edit',
                    iconSize: 'large'
                }
            },

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
                reset: {
                    ngClick: 'formReset()',
                    ngDisabled: true //Disabled when $pristine
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
                            icon: 'icon-plus',
                            awToolTip: 'Add a new user'
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
                            icon: 'icon-plus',
                            label: 'Add',
                            awToolTip: 'Add new administrator'
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
