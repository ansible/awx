/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Credentials.js
 *  Form definition for Credential model
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
                editRequired: true,
                autocomplete: false
                },
            description: { 
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false
                },
            kind: {
                label: 'Kind',
                type: 'radio',  // FIXME: Make select, pull from OPTIONS request
                options: [{ label: 'Machine', value: 'ssh' }, { label: 'SCM', value: 'scm'}, { label: 'AWS', value: 'aws'}, { label: 'Rackspace', value: 'rax'}],
                //ngChange: 'selectCategory()'
                },
            "username": {
                label: 'Username',
                type: 'text',
                addRequired: false,
                editRequired: false,
                autocomplete: false
                },
            "password": {
                label: 'Password',
                type: 'password',
                addRequired: false,
                editRequired: false,
                ngChange: "clearPWConfirm('password_confirm')",
                ask: true,
                clear: true,
                associated: 'password_confirm',
                autocomplete: false
                },
            "password_confirm": {
                label: 'Confirm Password',
                type: 'password',
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'password',
                autocomplete: false
                },
            "ssh_key_data": {
                label: 'SSH Private Key',
                type: 'textarea',
                addRequired: false,
                editRequired: false,
                'class': 'ssh-key-field',
                rows: 10,
                xtraWide: true
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
                editRequired: false,
                autocomplete: false
                },
            "sudo_password": {
                label: 'Sudo Password',
                type: 'password',
                addRequired: false,
                editRequired: false,
                ngChange: "clearPWConfirm('sudo_password_confirm')",
                ask: true,
                clear: true,
                associated: 'sudo_password_confirm',
                autocomplete: false
                },
            "sudo_password_confirm": {
                label: 'Confirm Sudo Password',
                type: 'password',
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'sudo_password',
                autocomplete: false
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

            }
            
    }); //InventoryForm

