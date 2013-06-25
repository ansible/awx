/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Permissions.js
 *
 *  Form definition for Projects model
 *
 *  
 */
angular.module('PermissionFormDefinition', [])
    .value(
    'PermissionsForm', {
        
        addTitle: 'Add Permission',                             //Title in add mode
        editTitle: '{{ name }}',                                //Title in edit mode
        name: 'permission',                                     //entity or model name in singular form
        well: true,                                             //Wrap the form with TB well/           

        fields: {
            category: {
                label: 'Permission Type',
                type: 'radio',
                options: [{ label: 'Inventory', value: 'Inventory' }, { label: 'Deployment', value: 'Deploy'}],
                ngChange: 'selectCategory()'
                },
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
            user: {
                label: 'User', 
                type: 'hidden'
                },
            team: {
                label: 'Team',
                type: 'hidden'
                },
            project: {
                label: 'Project',
                type: 'lookup',
                sourceModel: 'project',
                sourceField: 'name',
                ngShow: "category == 'Deploy'",
                ngClick: 'lookUpProject()',
                addRequired: false,
                editRequired: false
                },
            inventory: {
                label: 'Inventory',
                type: 'lookup',
                sourceModel: 'inventory',
                sourceField: 'name',
                ngClick: 'lookUpInventory()',
                addRequired: false,
                editRequired: false
                },
            permission_type: {
                label: 'Permission',
                type: 'radio',
                options: [
                    {label: 'Admin', value: 'admin', ngShow: "category == 'Inventory'" },
                    {label: 'Read', value: 'read', ngShow: "category == 'Inventory'" },
                    {label: 'Write', value: 'write', ngShow: "category == 'Inventory'" },
                    {label: 'Run', value: 'run', ngShow: "category == 'Deploy'" },
                    {label: 'Check', value: 'check', ngShow: "category == 'Deploy'" }
                    ]
                }
                /* ,
            deployment_permission_type: {
                label: 'Permission',
                type: 'radio',
                ngShow: "category == 'Deploy'",
                options: [
                    {label: 'Deploy', value: 'PERM_INVENTORY_DEPLOY'},
                    {label: 'Check', value: 'PERM_INVENTORY_CHECK'}
                    ]
                }*/
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

            }

    }); // Form