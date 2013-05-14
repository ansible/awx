/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Credentials.js
 *  Form definition for Credential model
 *
 *
 */
angular.module('CredentialFormDefinition', [])
    .value(
    'CredentialForm', {
        
        addTitle: 'Create Credential',                             //Legend in add mode
        editTitle: '{{ name }}',                                   //Legend in edit mode
        name: 'credential',
        well: true,

        fields: {
            name: {
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true
                },
            description: { 
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false
                },
            "ssh_username": {
                label: 'SSH Username',
                type: 'text',
                addRequired: false,
                editRequired: false
                },
            "ssh_password": {
                label: 'SSH Password',
                type: 'password',
                addRequired: false,
                editRequired: false,
                ngChange: "clearPWConfirm('ssh_password_confirm')",
                ask: true,
                clear: true,
                associated: 'ssh_password_confirm'
                },
            "ssh_password_confirm": {
                label: 'Confirm SSH Password',
                type: 'password',
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'ssh_password'
                },
            "ssh_key_data": {
                label: 'SSH Key',
                type: 'textarea',
                addRequired: false,
                editRequired: false,
                rows: 10
                },
            "ssh_key_unlock": {
                label: 'Key Password',
                type: 'password',
                addRequired: false,
                editRequired: false,
                ngChange: "clearPWConfirm('ssh_key_unlock_confirm')",
                associated: 'ssh_key_unlock_confirm',
                ask: true,
                clear: true
                },
            "ssh_key_unlock_confirm": {
                label: 'Confirm Key Password',
                type: 'password',
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'ssh_key_unlock'
                },
            "sudo_username": {
                label: 'Sudo Username',
                type: 'text',
                addRequired: false,
                editRequired: false
                },
            "sudo_password": {
                label: 'Sudo Password',
                type: 'password',
                addRequired: false,
                editRequired: false,
                ngChange: "clearPWConfirm('sudo_password_confirm')",
                ask: true,
                clear: true,
                associated: 'sudo_password_confirm'
                },
            "sudo_password_confirm": {
                label: 'Confirm Sudo Password',
                type: 'password',
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'sudo_password'
                },
            user: {
                label: 'User',
                type: 'lookup',
                sourceModel: 'user',
                sourceField: 'username',
                addRequired: false,
                editRequired: false,
                ngClick: 'lookUpUser()'
                },
            team: {
                label: 'Team',
                type: 'lookup',
                sourceModel: 'team',
                sourceField: 'name',
                addRequired: false,
                editRequired: false,
                ngClick: 'lookUpTeam()'
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

            }
            
    }); //InventoryForm

