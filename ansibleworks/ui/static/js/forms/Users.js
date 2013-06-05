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

        fields: {
            username: {
                label: 'Username',
                type: 'text',
                addRequired: true,
                editRequired: true
                },
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
                editRequired: true
                },
            password: {
                label: 'Password',
                type: 'password',
                addRequired: true,
                editRequired: false,
                ngChange: "clearPWConfirm('password_confirm')"
                },
            password_confirm: {
                label: 'Confirm Password',
                type: 'password',
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'password'
                },
            is_superuser: {
                label: 'Superuser?',
                type: 'checkbox',
                trueValue: 'true',
                falseValue: 'false',
                default: 'false',
                ngShow: "current_user['is_superuser'] == true"
                }
            },

        buttons: { //for now always generates <button> tags 
            save: { 
                label: 'Save', 
                icon: 'icon-ok',
                class: 'btn-success',
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                label: 'Reset',
                icon: 'icon-remove',
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
                        class: 'btn-success',
                        awToolTip: 'Edit the credential'
                        },
                    delete: {
                        label: 'Delete',
                        ngClick: "delete('credentials', \{\{ credential.id \}\}, '\{\{ credential.name \}\}', 'credentials')",
                        icon: 'icon-remove',
                        class: 'btn-danger',
                        awToolTip: 'Delete the credential'
                        }
                    }

                },
                
            admin_of_organizations: {                                       // Assumes a plural name (e.g. things)
                type: 'collection',
                title: 'Admin of Organizations',
                iterator: 'adminof',                                        // Singular form of name (e.g.  thing)
                open: false,                                                // Open accordion on load?
                base: '/organizations',
                
                fields: {
                    name: {
                        key: true,
                        label: 'Name'
                        },
                    description: {
                        label: 'Description'
                        },
                    }
                },

            organizations:  {
                type: 'collection',
                title: 'Organizations',
                iterator: 'organization',
                open: false,
                
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

