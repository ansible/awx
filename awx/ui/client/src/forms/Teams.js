/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

  /**
 * @ngdoc function
 * @name forms.function:Teams
 * @description This form is for adding/editing teams
*/

export default
    angular.module('TeamFormDefinition', [])
        .value('TeamForm', {

            addTitle: 'New Team', //Legend in add mode
            editTitle: '{{ name }}', //Legend in edit mode
            name: 'team',
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
                },
                organization: {
                    label: 'Organization',
                    type: 'lookup',
                    sourceModel: 'organization',
                    sourceField: 'name',
                    addRequired: true,
                    editRequire: false,
                    ngClick: 'lookUpOrganization()',
                    awRequiredWhen: {
                        variable: "orgrequired",
                        init: true
                    }
                }
            },

            buttons: {
                save: {
                    ngClick: 'formSave()',
                    ngDisabled: true
                },
                cancel: {
                    ngClick: 'formCancel()'
                }
            },

            related: {
                /*
                permissions: {
                    basePath: 'teams/:id/access_list/',
                    type: 'collection',
                    title: 'Permissions',
                    iterator: 'permission',
                    index: false,
                    open: false,
                    searchType: 'select',
                    actions: {
                        add: {
                            ngClick: "addPermission",
                            label: 'Add',
                            awToolTip: 'Add a permission',
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ADD'
                        }
                    }
                },
                */


                credentials: {
                    type: 'collection',
                    title: 'Credentials',
                    iterator: 'credential',
                    open: false,
                    index: false,

                    actions: {
                        add: {
                            ngClick: "add('credentials')",
                            label: 'Add',
                            add: 'Add a new credential',
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ADD'
                        }
                    },

                    fields: {
                        name: {
                            key: true,
                            label: 'Name'
                        },
                        description: {
                            label: 'Description'
                        }
                    },

                    fieldActions: {
                        edit: {
                            label: 'Edit',
                            ngClick: "edit('credentials', credential.id, credential.name)",
                            icon: 'icon-edit',
                            awToolTip: 'Modify the credential',
                            'class': 'btn btn-default'
                        },
                        "delete": {
                            label: 'Delete',
                            ngClick: "delete('credentials', credential.id, credential.name, 'credential')",
                            icon: 'icon-trash',
                            "class": 'btn-danger',
                            awToolTip: 'Remove the credential'
                        }
                    }
                },

                projects: {
                    type: 'collection',
                    title: 'Projects',
                    iterator: 'project',
                    open: false,
                    index: false,

                    actions: {
                        add: {
                            ngClick: "add('projects')",
                            label: 'Add',
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ADD'
                        }
                    },

                    fields: {
                        name: {
                            key: true,
                            label: 'Name'
                        },
                        description: {
                            label: 'Description'
                        }
                    },

                    fieldActions: {
                        edit: {
                            label: 'Edit',
                            ngClick: "edit('projects', project.id, project.name)",
                            icon: 'icon-edit',
                            awToolTip: 'Modify the project',
                            'class': 'btn btn-default'
                        },
                        "delete": {
                            label: 'Delete',
                            ngClick: "delete('projects', project.id, project.name, 'project')",
                            icon: 'icon-trash',
                            "class": 'btn-danger',
                            awToolTip: 'Remove the project'
                        }
                    }
                },

                users: {
                    type: 'collection',
                    title: 'Users',
                    iterator: 'user',
                    open: false,
                    index: false,

                    actions: {
                        add: {
                            ngClick: "add('users')",
                            label: 'Add',
                            awToolTip: 'Add a user',
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
                            awToolTip: 'Edit user',
                            'class': 'btn btn-default'
                        },
                        "delete": {
                            label: 'Delete',
                            ngClick: "delete('users', user.id, user.username, 'user')",
                            icon: 'icon-terash',
                            "class": 'btn-danger',
                            awToolTip: 'Remove user'
                        }
                    }
                }

            }

        }); //InventoryForm
