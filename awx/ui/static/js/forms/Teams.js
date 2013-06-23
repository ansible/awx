/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Teams.js
 *  Form definition for Team model
 *
 *  
 */
angular.module('TeamFormDefinition', [])
    .value(
    'TeamForm', {
        
        addTitle: 'Create Team',                             //Legend in add mode
        editTitle: '{{ name }}',                                  //Legend in edit mode
        name: 'team',
        well: true,

        fields: {
            name: {
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                capitalize: true
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
                editRequired: true,
                ngClick: 'lookUpOrganization()'
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
                icon: 'icon-remove',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: { //related colletions (and maybe items?)
            
            users:  {
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
                        ngClick: "edit('users', \{\{ user.id \}\}, '\{\{ user.username \}\}')",
                        icon: 'icon-edit',
                        "class": 'btn-success',
                        awToolTip: 'Edit user'
                        },
                    "delete": {
                        label: 'Delete',
                        ngClick: "delete('users', \{\{ user.id \}\}, '\{\{ user.username \}\}', 'users')",
                        icon: 'icon-remove',
                        "class": 'btn-danger',
                        awToolTip: 'Remove user'
                        }
                    }
                },

            credentials:  {
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
                        ngClick: "edit('credentials', \{\{ credential.id \}\}, '\{\{ credential.name \}\}')",
                        icon: 'icon-edit',
                        "class": 'btn-success',
                        awToolTip: 'Modify the credential'
                        },
                    "delete": {
                        label: 'Delete',
                        ngClick: "delete('credentials', \{\{ credential.id \}\}, '\{\{ credential.name \}\}', 'credentials')",
                        icon: 'icon-remove',
                        "class": 'btn-danger',
                        awToolTip: 'Remove the credential'
                        }
                    }
                },

            projects:  {
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
                        ngClick: "edit('projects', \{\{ project.id \}\}, '\{\{ project.name \}\}')",
                        icon: 'icon-edit',
                        "class": 'btn-success',
                        awToolTip: 'Modify the project'
                        },
                    "delete": {
                        label: 'Delete',
                        ngClick: "delete('projects', \{\{ project.id \}\}, '\{\{ project.name \}\}', 'projects')",
                        icon: 'icon-remove',
                        "class": 'btn-danger',
                        awToolTip: 'Remove the project'
                        }
                    }
                }

            }
            
    }); //InventoryForm

