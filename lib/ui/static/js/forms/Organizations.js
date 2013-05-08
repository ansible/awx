/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Organization.js
 *  Form definition for Organization model
 *
 *
 */
angular.module('OrganizationFormDefinition', [])
    .value(
    'OrganizationForm', {
        
        addTitle: 'Create Organization',                        //Title in add mode
        editTitle: '{{ name }}',                                //Title in edit mode
        name: 'organization',                                   //entity or model name in singular form
        well: true, 			                                //Wrap the form with TB well/		  	

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
                }
            },

        buttons: { //for now always generates <button> tags	
            save: { 
                label: 'Save', 
                icon: 'icon-ok',
                class: 'btn btn-success',
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                label: 'Reset',
                icon: 'icon-remove',
                class: 'btn',
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
                        icon: 'icon-plus'
                        },
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
                        ngClick: "edit('users', \{\{ user.id \}\}, '\{\{ user.username \}\}')",
                        icon: 'icon-edit'
                        },
                    delete: {
                        ngClick: "delete('users', \{\{ user.id \}\}, '\{\{ user.username \}\}', 'users')",
                        icon: 'icon-remove',
                        class: 'btn-danger'
                        }
                    }
                },

            admins: {                                                     // Assumes a plural name (e.g. things)
                type: 'collection',
                title: 'Administrators',
                iterator: 'admin',                                        // Singular form of name (e.g.  thing)
                open: false,                                              // Open accordion on load?
                actions: {                                                // Actions displayed top right of list
                    add: {
                        ngClick: "add('admins')",
                        icon: 'icon-plus'
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
                fieldActions: {                                           // Actions available on each row
                    delete: {
                        ngClick: "delete('admins', \{\{ admin.id \}\}, '\{\{ admin.username \}\}', 'administrators')",
                        icon: 'icon-remove',
                        class: 'btn-danger'
                        }
                    }
                }
                
            }

    }); //OrganizationForm

    