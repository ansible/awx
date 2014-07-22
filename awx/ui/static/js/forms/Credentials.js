/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Credentials.js
 *  Form definition for Credential model
 *
 */
angular.module('CredentialFormDefinition', [])
    .value('CredentialForm', {

        addTitle: 'Create Credential', //Legend in add mode
        editTitle: '{{ name }}', //Legend in edit mode
        name: 'credential',
        well: true,
        forceListeners: true,

        actions: {
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                mode: 'edit'
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
                label: "Does this credential belong to a team or user?",
                type: 'radio_group',
                ngChange: "ownerChange()",
                options: [{
                    label: 'User',
                    value: 'user',
                    selected: true
                }, {
                    label: 'Team',
                    value: 'team'
                }],
                awPopOver: "<p>A credential must be associated with either a user or a team. Choosing a user allows only the selected user access " +
                    "to the credential. Choosing a team shares the credential with all team members.</p>",
                dataTitle: 'Owner',
                dataPlacement: 'right',
                dataContainer: "body"
            },
            user: {
                label: 'User that owns this credential',
                type: 'lookup',
                sourceModel: 'user',
                sourceField: 'username',
                ngClick: 'lookUpUser()',
                ngShow: "owner == 'user'",
                awRequiredWhen: {
                    variable: "user_required",
                    init: "false"
                }
            },
            team: {
                label: 'Team that owns this credential',
                type: 'lookup',
                sourceModel: 'team',
                sourceField: 'name',
                ngClick: 'lookUpTeam()',
                ngShow: "owner == 'team'",
                awRequiredWhen: {
                    variable: "team_required",
                    init: "false"
                }
            },
            kind: {
                label: 'Type',
                excludeModal: true,
                type: 'select',
                ngOptions: 'kind.label for kind in credential_kind_options',
                ngChange: 'kindChange()',
                addRequired: true,
                editRequired: true,
                helpCollapse: [{
                    hdr: 'Select a Credential Type',
                    content: '<dl>\n' +
                        '<dt>Machine</dt>\n' +
                        '<dd>Authentication for remote machine access. This can include SSH keys, usernames, passwords, ' +
                        'and sudo information. Machine credentials are used when submitting jobs to run playbooks against ' +
                        'remote hosts.</dd>' +
                        '<dt>Source Control</dt>\n' +
                        '<dd>Used to check out and synchronize playbook repositories with a remote source control ' +
                        'management system such as Git, Subversion (svn), or Mercurial (hg). These credentials are ' +
                        'used on the Projects tab.</dd>\n' +
                        '<dt>Amazon Web Services</dt>\n' +
                        '<dd>Access keys for Amazon Web Services used for inventory management or deployment.</dd>\n' +
                        '<dt>Rackspace</dt>\n' +
                        '<dd>Access information for Rackspace Cloud used for inventory management or deployment.</dd>\n' +
                        '<dt>Google Compute Engine</dt>\n' +
                        '<dd>Credentials for Google Compute Engine, used for inventory management or deployment.</dd>\n' +
                        '<dt>VMWare</dt>\n' +
                        '<dd>Access information for VMWare vSphere used for inventory management or deployment.</dd>\n' +
                        '</dl>\n'
                }]
            },
            access_key: {
                label: 'Access Key',
                type: 'text',
                ngShow: "kind.value == 'aws'",
                awRequiredWhen: {
                    variable: "aws_required",
                    init: false
                },
                autocomplete: false,
                apiField: 'username'
            },
            secret_key: {
                label: 'Secret Key',
                type: 'password',
                ngShow: "kind.value == 'aws'",
                awRequiredWhen: {
                    variable: "aws_required",
                    init: false
                },
                autocomplete: false,
                ask: false,
                clear: false,
                apiField: 'passwowrd'
            },
            "host": {
                label: 'Host',
                type: 'text',
                ngShow: "kind.value == 'vmware'",
                autocomplete: false
            },
            "username": {
                labelBind: 'usernameLabel',
                type: 'text',
                ngShow: "kind.value && kind.value !== 'aws'",
                awRequiredWhen: {
                    variable: 'rackspace_required',
                    init: false
                },
                autocomplete: false
            },
            "api_key": {
                label: 'API Key',
                type: 'password',
                ngShow: "kind.value == 'rax'",
                awRequiredWhen: {
                    variable: "rackspace_required",
                    init: false
                },
                autocomplete: false,
                ask: false,
                clear: false,
                apiField: 'passwowrd'
            },
            "password": {
                label: 'Password',
                type: 'password',
                ngShow: "kind.value == 'scm' || kind.value == 'vmware'",
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
                ngShow: "kind.value == 'scm' || kind.value == 'vmware'",
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
                ngShow: "kind.value == 'ssh' || kind.value == 'scm' || kind.value == 'gce'",
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
                askShow: "kind.value == 'ssh'", //Only allow ask for machine credentials
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
            },
            "project": {
                label: "Project",
                type: 'text',
                ngShow: "kind.value == 'gce'",
                addRequired: false,
                editRequired: false,
                autocomplete: false
            },
            "vault_password": {
                label: "Vault Password",
                type: 'password',
                ngShow: "kind.value == 'ssh'",
                addRequired: false,
                editRequired: false,
                ngChange: "clearPWConfirm('vault_password_confirm')",
                ask: true,
                clear: true,
                associated: 'vault_password_confirm',
                autocomplete: false
            },
            "vault_password_confirm": {
                label: "Confirm Vault Password",
                type: 'password',
                ngShow: "kind.value == 'ssh'",
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'vault_password',
                autocomplete: false
            }
        },

        buttons: {
            save: {
                label: 'Save',
                ngClick: 'formSave()', //$scope.function to call on click, optional
                ngDisabled: true //Disable when $pristine or $invalid, optional
            },
            reset: {
                ngClick: 'formReset()',
                ngDisabled: true //Disabled when $pristine
            }
        },

        related: {}

    });
