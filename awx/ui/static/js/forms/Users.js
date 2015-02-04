/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Users.js
 *  Form definition for User model
 *
 *
 */
  /**
 * @ngdoc function
 * @name forms.function:Users
 * @description This form is for adding/editing users
*/

export default
    angular.module('UserFormDefinition', [])
        .value('UserForm', {

            addTitle: 'Create User',
            editTitle: '{{ username }}',
            name: 'user',
            well: true,
            forceListeners: true,
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
                first_name: {
                    label: 'First Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: true
                },
                last_name: {
                    label: 'Last Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: true
                },
                email: {
                    label: 'Email',
                    type: 'email',
                    addRequired: true,
                    editRequired: true,
                    autocomplete: false
                },
                organization: {
                    label: 'Organization',
                    type: 'lookup',
                    sourceModel: 'organization',
                    sourceField: 'name',
                    ngClick: 'lookUpOrganization()',
                    excludeMode: 'edit',
                    awRequiredWhen: {
                        variable: "orgrequired",
                        init: true
                    }
                },
                username: {
                    label: 'Username',
                    type: 'text',
                    awRequiredWhen: {
                        variable: "not_ldap_user",
                        init: true
                    },
                    autocomplete: false
                },
                password: {
                    label: 'Password',
                    type: 'password',
                    ngShow: 'ldap_user == false',
                    addRequired: true,
                    editRequired: false,
                    ngChange: "clearPWConfirm('password_confirm')",
                    autocomplete: false,
                    chkPass: true
                },
                password_confirm: {
                    label: 'Confirm Password',
                    type: 'password',
                    ngShow: 'ldap_user == false',
                    addRequired: false,
                    editRequired: false,
                    awPassMatch: true,
                    associated: 'password',
                    autocomplete: false
                },
                is_superuser: {
                    label: 'Superuser (User has full system administration privileges.)',
                    type: 'checkbox',
                    trueValue: 'true',
                    falseValue: 'false',
                    "default": 'false',
                    ngShow: "current_user['is_superuser'] == true"
                },
                ldap_user: {
                    label: 'Created by LDAP',
                    type: 'checkbox',
                    readonly: true
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
                    index: false,

                    actions: {
                        add: {
                            ngClick: "add('credentials')",
                            icon: 'icon-plus',
                            label: 'Add',
                            awToolTip: 'Add a credential for this user'
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
                            awToolTip: 'Edit the credential',
                            'class': 'btn btn-default'
                        },
                        "delete": {
                            label: 'Delete',
                            ngClick: "delete('credentials', credential.id, credential.name, 'credentials')",
                            icon: 'icon-trash',
                            "class": 'btn-danger',
                            awToolTip: 'Delete the credential'
                        }
                    }
                },

                permissions: {
                    type: 'collection',
                    title: 'Permissions',
                    iterator: 'permission',
                    open: false,
                    index: false,

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

                admin_of_organizations: { // Assumes a plural name (e.g. things)
                    type: 'collection',
                    title: 'Admin of Organizations',
                    iterator: 'adminof', // Singular form of name (e.g.  thing)
                    open: false, // Open accordion on load?
                    index: false,
                    base: '/organizations',

                    actions: {},

                    fields: {
                        name: {
                            key: true,
                            label: 'Name'
                        },
                        description: {
                            label: 'Description'
                        }
                    }
                },

                organizations: {
                    type: 'collection',
                    title: 'Organizations',
                    iterator: 'organization',
                    index: false,
                    open: false,

                    actions: {},

                    fields: {
                        name: {
                            key: true,
                            label: 'Name'
                        },
                        description: {
                            label: 'Description'
                        }
                    }
                },

                teams: {
                    type: 'collection',
                    title: 'Teams',
                    iterator: 'team',
                    open: false,
                    index: false,

                    actions: {},

                    fields: {
                        name: {
                            key: true,
                            label: 'Name'
                        },
                        description: {
                            label: 'Description'
                        }
                    }
                }
            }

        }); //UserForm
