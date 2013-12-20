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
        forceListeners: true,
        
        actions: {
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                mode: 'edit',
                ngShow: "user_is_superuser"
                }    
            },
            
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
            owner: {
                label: 'Owned By?',
                type: 'radio',
                ngChange: "ownerChange()",
                addRequired: true,
                editRequired: true,
                options: [
                    { label: 'User', value: 'user' },
                    { label: 'Team', value: 'team' }
                    ],
                awPopOver: "<p>A credential must be associated with either a user or a team. Choosing a user allows only the selected user access " + 
                    "to the credential. Choosing a team shares the credential with all team members.</p>",
                dataTitle: 'Owner',
                dataPlacement: 'right',
                dataContainer: "body"
                },
            user: {
                label: 'User',
                type: 'lookup',
                sourceModel: 'user',
                sourceField: 'username',
                ngClick: 'lookUpUser()',
                ngShow: "owner == 'user'",
                awRequiredWhen: { variable: "user_required", init: "false" }
                },
            team: {
                label: 'Team',
                type: 'lookup',
                sourceModel: 'team',
                sourceField: 'name',
                ngClick: 'lookUpTeam()',
                ngShow: "owner == 'team'",
                awRequiredWhen: { variable: "team_required", init: "false" }
                },
            kind: {
                label: 'Type',
                excludeModal: true,
                type: 'select',
                ngOptions: 'kind.label for kind in credential_kind_options',
                ngChange: 'kindChange()',
                addRequired: true, 
                editRequired: true,
                helpCollapse: [
                    { hdr: 'Credential Type',
                      content: '<p>Choose a type for this credential: ' +
                               '<dl>\n' +
                               '<dt>AWS</dt>\n' +
                               '<dd>Access keys for Amazon Web Services used for inventory management or deployment.</dd>\n' +
                               '<dt>Machine</dt>\n' +
                               '<dd>Authentication for remote machine access. This can include SSH keys, usernames, passwords, ' +
                               'and sudo information. Machine credentials are used when submitting jobs to run playbooks against ' +
                               'remote hosts.</dd>' +
                               '<dt>Rackspace</dt>\n' + 
                               '<dd>Access information for Rackspace Cloud used for inventory management or deployment.</dd>\n' + 
                               '<dt>SCM</dt>\n' +
                               '<dd>Used to check out and synchronize playbook repositories with a remote source control ' +
                               'management system such as Git, Subversion (svn), or Mercurial (hg). These credentials are ' +
                               'used on the Projects tab.</dd>\n' +
                               '</dl>\n'
                    }]
                },
            access_key: {
                label: 'Access Key',
                type: 'text',
                ngShow: "kind.value == 'aws'",
                awRequiredWhen: { variable: "aws_required", init: false },
                autocomplete: false,
                apiField: 'username'
                },
            secret_key: {
                label: 'Secret Key',
                type: 'password',
                ngShow: "kind.value == 'aws'",
                awRequiredWhen: { variable: "aws_required", init: false },
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
            "api_key": {
                label: 'API Key',
                type: 'password',
                ngShow: "kind.value == 'rax'",
                awRequiredWhen: { variable: "rackspace_required", init: false },
                autocomplete: false,
                ask: false,
                clear: false,
                apiField: 'passwowrd'
                },
            "password": {
                label: 'Password',
                type: 'password',
                ngShow: "kind.value == 'scm'",
                addRequired: false,
                editRequired: false,
                ngChange: "clearPWConfirm('password_confirm')",
                ask: false,
                clear: false,
                associated: 'password_confirm',
                autocomplete: false
                },
            "password_confirm": {
                label: 'Confirm Password',
                type: 'password',
                ngShow: "kind.value == 'scm'",
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'password',
                autocomplete: false
                },
            "ssh_password": {
                label: 'SSH Password',
                type: 'password',
                ngShow: "kind.value == 'ssh'",
                ngChange: "clearPWConfirm('ssh_password_confirm')",
                addRequired: false,
                editRequired: false,
                ask: true,
                clear: true,
                associated: 'ssh_password_confirm',
                autocomplete: false
                },
            "ssh_password_confirm": {
                label: 'Confirm SSH Password',
                type: 'password',
                ngShow: "kind.value == 'ssh'",
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'ssh_password',
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
                ngShow: "kind.value == 'ssh' || kind.value == 'scm'",
                addRequired: false,
                editRequired: false,
                ngChange: "clearPWConfirm('ssh_key_unlock_confirm')",
                associated: 'ssh_key_unlock_confirm',
                ask: true,
                askShow: "kind.value == 'ssh'",   //Only allow ask for machine credentials
                clear: true
                },
            "ssh_key_unlock_confirm": {
                label: 'Confirm Key Password',
                type: 'password',
                ngShow: "kind.value == 'ssh'  || kind.value == 'scm'",
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
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: { //related colletions (and maybe items?)

            }
            
    }); //InventoryForm

