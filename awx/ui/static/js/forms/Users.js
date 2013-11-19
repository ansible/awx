/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Users.js
 *  Form definition for User model
 *
 *  
 */
angular.module('UserFormDefinition', [])
    .value(
    'UserForm', {
        
        addTitle: 'Create User',                             //Legend in add mode
        editTitle: '{{ username }}',                         //Legend in edit mode
        name: 'user',                                        //Form name attribute
        well: true,                                          //Wrap the form with TB well
        forceListeners: true,

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
                awRequiredWhen: { variable: "orgrequired", init: true }
                },
            username: {
                label: 'Username',
                type: 'text',
                awRequiredWhen: { variable: "not_ldap_user", init: true },
                autocomplete: false
                },
            ldap_user: {
                label: 'Created by LDAP?', 
                type: 'checkbox',
                readonly: true
                },
            password: {
                label: 'Password',
                type: 'password',
                ngShow: 'ldap_user == false',
                awRequiredWhen: { variable: "not_ldap_user", init: true },
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
                label: 'Superuser?',
                type: 'checkbox',
                trueValue: 'true',
                falseValue: 'false',
                "default": 'false',
                ngShow: "current_user['is_superuser'] == true"
                }
            },

        buttons: { //for now always generates <button> tags 
            save: { 
                label: 'Save', 
                icon: 'icon-ok',
                "class": 'btn-success',
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                label: 'Reset',
                icon: 'icon-trash',
                'class': 'btn btn-default',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: { //related colletions (and maybe items?)
            
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
                        awToolTip: 'Add a credential for this user'
                        },
                    reset: {
                        dataPlacement: 'top',
                        icon: "icon-undo",
                        mode: 'all',
                        'class': 'btn-xs btn-primary',
                        awToolTip: "Reset the search filter",
                        ngClick: "resetSearch('credential')",
                        iconSize: 'large'
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
                        ngClick: "edit('credentials', \{\{ credential.id \}\}, '\{\{ credential.name \}\}')",
                        icon: 'icon-edit',
                        awToolTip: 'Edit the credential',
                        'class': 'btn btn-default'
                        },
                    "delete": {
                        label: 'Delete',
                        ngClick: "delete('credentials', \{\{ credential.id \}\}, '\{\{ credential.name \}\}', 'credentials')",
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
                
                actions: { 
                    add: {
                        ngClick: "add('permissions')",
                        icon: 'icon-plus',
                        label: 'Add',
                        awToolTip: 'Add a permission for this user',
                        ngShow: 'PermissionAddAllowed'
                        },
                    reset: {
                        dataPlacement: 'top',
                        icon: "icon-undo",
                        mode: 'all',
                        'class': 'btn-xs btn-primary',
                        awToolTip: "Reset the search filter",
                        ngClick: "resetSearch('permission')",
                        iconSize: 'large'
                        }
                    },

                fields: {
                    name: {
                        key: true, 
                        label: 'Name',
                        ngClick: "edit('permissions', \{\{ permission.id \}\}, '\{\{ permission.name \}\}')"
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
                        ngClick: "edit('permissions', \{\{ permission.id \}\}, '\{\{ permission.name \}\}')",
                        icon: 'icon-edit',
                        awToolTip: 'Edit the permission',
                        'class': 'btn btn-default'
                        },
                    
                    "delete": {
                        label: 'Delete',
                        ngClick: "delete('permissions', \{\{ permission.id \}\}, '\{\{ permission.name \}\}', 'permissions')",
                        icon: 'icon-trash',
                        "class": 'btn-danger',
                        awToolTip: 'Delete the permission',
                        ngShow: 'PermissionAddAllowed'
                        }
                    }

                },
                
            admin_of_organizations: {                                       // Assumes a plural name (e.g. things)
                type: 'collection',
                title: 'Admin of Organizations',
                iterator: 'adminof',                                        // Singular form of name (e.g.  thing)
                open: false,                                                // Open accordion on load?
                base: '/organizations',
                
                actions: {
                    reset: {
                        dataPlacement: 'top',
                        icon: "icon-undo",
                        mode: 'all',
                        'class': 'btn-xs btn-primary',
                        awToolTip: "Reset the search filter",
                        ngClick: "resetSearch('adminof')",
                        iconSize: 'large'
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
                    }
                },

            organizations:  {
                type: 'collection',
                title: 'Organizations',
                iterator: 'organization',
                open: false,
                
                actions: {
                    reset: {
                        dataPlacement: 'top',
                        icon: "icon-undo",
                        mode: 'all',
                        'class': 'btn-xs btn-primary',
                        awToolTip: "Reset the search filter",
                        ngClick: "resetSearch('organization')",
                        iconSize: 'large'
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
                    }
                },

            teams: {
                type: 'collection',
                title: 'Teams',
                iterator: 'team',
                open: false,

                actions: {
                    reset: {
                        dataPlacement: 'top',
                        icon: "icon-undo",
                        mode: 'all',
                        'class': 'btn-xs btn-primary',
                        awToolTip: "Reset the search filter",
                        ngClick: "resetSearch('team')",
                        iconSize: 'large'
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
                    }
                },

            projects: {
                type: 'collection',
                title: 'Projects',
                iterator: 'project',
                open: false,

                actions: {
                    reset: {
                        dataPlacement: 'top',
                        icon: "icon-undo",
                        mode: 'all',
                        'class': 'btn-xs btn-primary',
                        awToolTip: "Reset the search filter",
                        ngClick: "resetSearch('project')",
                        iconSize: 'large'
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
                    }
                }
                
            }

    }); //UserForm

