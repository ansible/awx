/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Teams.js
 *
 *  Form definition for Team model
 *
 */
angular.module('TeamFormDefinition', [])
    .value('TeamForm', {

        addTitle: 'Create Team', //Legend in add mode
        editTitle: '{{ name }}', //Legend in edit mode
        name: 'team',
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
            },
            organization: {
                label: 'Organization',
                type: 'lookup',
                sourceModel: 'organization',
                sourceField: 'name',
                ngClick: 'lookUpOrganization()',
                awRequiredWhen: {
                    variable: "teamrequired",
                    init: "true"
                }
            }
        },

        buttons: {
            save: {
                ngClick: 'formSave()',
                ngDisabled: true
            },
            reset: {
                ngClick: 'formReset()',
                ngDisabled: true
            }
        },

        related: {

            credentials: {
                type: 'collection',
                title: 'Credentials',
                iterator: 'credential',
                open: false,

                actions: {
                    add: {
                        ngClick: "add('credentials')",
                        icon: 'icon-plus',
                        label: 'Add',
                        add: 'Add a new credential'
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
                        ngClick: "delete('credentials', credential.id, credential.name, 'credentials')",
                        icon: 'icon-trash',
                        "class": 'btn-danger',
                        awToolTip: 'Remove the credential'
                    }
                }
            },

            permissions: {
                type: 'collection',
                title: 'Permissions',
                iterator: 'permission',
                open: false,

                actions: {
                    add: {
                        ngClick: "add('permissions')",
                        icon: 'icon-plus',
                        label: 'Add',
                        awToolTip: 'Add a permission for this user',
                        ngShow: 'PermissionAddAllowed'
                    }
                },

                fields: {
                    name: {
                        key: true,
                        label: 'Name',
                        ngClick: "edit('permissions', permission.id, permission.name)"
                    },
                    inventory: {
                        label: 'Inventory',
                        sourceModel: 'inventory',
                        sourceField: 'name',
                        ngBind: 'permission.summary_fields.inventory.name'
                    },
                    project: {
                        label: 'Project',
                        sourceModel: 'project',
                        sourceField: 'name',
                        ngBind: 'permission.summary_fields.project.name'
                    },
                    permission_type: {
                        label: 'Permission'
                    }
                },

                fieldActions: {
                    edit: {
                        label: 'Edit',
                        ngClick: "edit('permissions', permission.id, permission.name)",
                        icon: 'icon-edit',
                        awToolTip: 'Edit the permission',
                        'class': 'btn btn-default'
                    },

                    "delete": {
                        label: 'Delete',
                        ngClick: "delete('permissions', permission.id, permission.name, 'permissions')",
                        icon: 'icon-trash',
                        "class": 'btn-danger',
                        awToolTip: 'Delete the permission',
                        ngShow: 'PermissionAddAllowed'
                    }
                }

            },

            projects: {
                type: 'collection',
                title: 'Projects',
                iterator: 'project',
                open: false,

                actions: {
                    add: {
                        ngClick: "add('projects')",
                        icon: 'icon-plus',
                        label: 'Add'
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
                        ngClick: "delete('projects', project.id, project.name, 'projects')",
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

                actions: {
                    add: {
                        ngClick: "add('users')",
                        icon: 'icon-plus',
                        label: 'Add',
                        awToolTip: 'Add a user'
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
                        ngClick: "delete('users', user.id, user.username, 'users')",
                        icon: 'icon-terash',
                        "class": 'btn-danger',
                        awToolTip: 'Remove user'
                    }
                }
            }

        }

    }); //InventoryForm