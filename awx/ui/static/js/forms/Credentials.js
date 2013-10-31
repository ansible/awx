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
            user: {
                label: 'User',
                type: 'lookup',
                sourceModel: 'user',
                sourceField: 'username',
                ngClick: 'lookUpUser()',
                ngShow: "team == '' || team == null",
                awPopOver: "<p>A credential must be associated with either a user or a team. Choosing a user allows only the selected user access " + 
                    "to the credential.</p>",
                dataTitle: 'User',
                dataPlacement: 'right',
                dataContainer: "body"
                },
            team: {
                label: 'Team',
                type: 'lookup',
                sourceModel: 'team',
                sourceField: 'name',
                ngClick: 'lookUpTeam()',
                ngShow: "user == '' || user == null",
                awPopOver: "<p>A credential must be associated with either a user or a team. Choose a team to share a credential with " +
                    "all users in the team.</p>",
                dataTitle: 'Team',
                dataPlacement: 'right',
                dataContainer: "body"
                },
            kind: {
                label: 'Type',
                excludeModal: true,
                type: 'select',
                ngOptions: 'kind.label for kind in credential_kind_options',
                ngChange: 'kindChange()',
                addRequired: true, 
                editRequired: true
                },
            access_key: {
                label: 'Access Key',
                type: 'text',
                ngShow: "kind.value == 'aws'",
                awRequiredWhen: {variable: "aws_required", init: "false" },
                autocomplete: false,
                apiField: 'username'
                },
            secret_key: {
                label: 'Secrent Key',
                type: 'password',
                ngShow: "kind.value == 'aws'",
                awRequiredWhen: {variable: "aws_required", init: "false" },
                autocomplete: false,
                ask: false,
                clear: false,
                apiField: 'passwowrd'
                },
            "username": {
                labelBind: 'usernameLabel',
                type: 'text',
                ngShow: "kind.value && kind.value !== 'aws'",
                awRequiredWhen: {variable: 'rackspace_required', init: false },
                autocomplete: false
                },
            "password": {
                labelBind: 'passwordLabel',
                type: 'password',
                ngShow: "kind.value && kind.value !== 'aws'",
                awRequiredWhen: {variable: 'rackspace_required', init: false },
                ngChange: "clearPWConfirm('password_confirm')",
                ask: false,
                clear: false,
                associated: 'password_confirm',
                autocomplete: false
                },
            "password_confirm": {
               labelBind: 'passwordConfirmLabel',
                type: 'password',
                ngShow: "kind.value && kind.value !== 'aws'",
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'password',
                autocomplete: false
                },
            "ssh_key_data": {
                labelBind: 'sshKeyDataLabel',
                type: 'textarea',
                ngShow: "kind.value == 'ssh' || kind.value == 'scm'",
                addRequired: false,
                editRequired: false,
                'class': 'ssh-key-field',
                rows: 10
                },
            "ssh_key_unlock": {
                label: 'Key Password',
                type: 'password',
                ngShow: "kind.value == 'ssh'",
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
                ngShow: "kind.value == 'ssh'",
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'ssh_key_unlock'
                },
            "sudo_username": {
                label: 'Sudo Username',
                type: 'text',
                ngShow: "kind.value == 'ssh'",
                addRequired: false,
                editRequired: false,
                autocomplete: false
                },
            "sudo_password": {
                label: 'Sudo Password',
                type: 'password',
                ngShow: "kind.value == 'ssh'",
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
                ngShow: "kind.value == 'ssh'",
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

