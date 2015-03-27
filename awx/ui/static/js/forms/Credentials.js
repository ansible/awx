/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Credentials.js
 *  Form definition for Credential model
 *
 */
 /**
 * @ngdoc function
 * @name forms.function:Credentials
 * @description This form is for adding/editing a Credential
*/

export default
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
                    ngOptions: 'kind.label for kind in credential_kind_options track by kind.value', //  select as label for value in array 'kind.label for kind in credential_kind_options',
                    ngChange: 'kindChange()',
                    addRequired: true,
                    editRequired: true,
                    awPopOver:'<dl>\n' +
                            '<dt>Machine</dt>\n' +
                            '<dd>Authentication for remote machine access. This can include SSH keys, usernames, passwords, ' +
                            'and sudo information. Machine credentials are used when submitting jobs to run playbooks against ' +
                            'remote hosts.</dd>' +
                            '<dt>Source Control</dt>\n' +
                            '<dd>Used to check out and synchronize playbook repositories with a remote source control ' +
                            'management system such as Git, Subversion (svn), or Mercurial (hg). These credentials are ' +
                            'used on the Projects tab.</dd>\n' +
                            '<dt>Others (Cloud Providers)</dt>\n' +
                            '<dd>Access keys for authenticating to the specific ' +
                            'cloud provider, usually used for inventory sync ' +
                            'and deployment.</dd>\n' +
                            '</dl>\n',
                    dataTitle: 'Type',
                    dataPlacement: 'right',
                    dataContainer: "body"
                    // helpCollapse: [{
                    //     hdr: 'Select a Credential Type',
                    //     content: '<dl>\n' +
                    //         '<dt>Machine</dt>\n' +
                    //         '<dd>Authentication for remote machine access. This can include SSH keys, usernames, passwords, ' +
                    //         'and sudo information. Machine credentials are used when submitting jobs to run playbooks against ' +
                    //         'remote hosts.</dd>' +
                    //         '<dt>Source Control</dt>\n' +
                    //         '<dd>Used to check out and synchronize playbook repositories with a remote source control ' +
                    //         'management system such as Git, Subversion (svn), or Mercurial (hg). These credentials are ' +
                    //         'used on the Projects tab.</dd>\n' +
                    //         '<dt>Others (Cloud Providers)</dt>\n' +
                    //         '<dd>Access keys for authenticating to the specific ' +
                    //         'cloud provider, usually used for inventory sync ' +
                    //         'and deployment.</dd>\n' +
                    //         '</dl>\n'
                    // }]
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
                    type: 'sensitive',
                    ngShow: "kind.value == 'aws'",
                    awRequiredWhen: {
                        variable: "aws_required",
                        init: false
                    },
                    autocomplete: false,
                    ask: false,
                    clear: false,
                    hasShowInputButton: true,
                    apiField: 'passwowrd'
                },
                "host": {
                    labelBind: 'hostLabel',
                    type: 'text',
                    ngShow: "kind.value == 'vmware'",
                    autocomplete: false,
                    awRequiredWhen: {
                        variable: 'host_required',
                        init: false
                    }
                },
                "username": {
                    labelBind: 'usernameLabel',
                    type: 'text',
                    ngShow: "kind.value && kind.value !== 'aws' && " +
                            "kind.value !== 'gce' && kind.value!=='azure'",
                    awRequiredWhen: {
                        variable: 'username_required',
                        init: false
                    },
                    autocomplete: false
                },
                "email_address": {
                    labelBind: 'usernameLabel',
                    type: 'email',
                    ngShow: "kind.value === 'gce'",
                    awRequiredWhen: {
                        variable: 'email_required',
                        init: false
                    },
                    autocomplete: false,
                    awPopOver: '<p>The email address assigned to the Google Compute Engine <b><i>service account.</b></i></p>',
                    dataTitle: 'Email',
                    dataPlacement: 'right',
                    dataContainer: "body"
                },
                "subscription_id": {
                    labelBind: "usernameLabel",
                    type: 'text',
                    ngShow: "kind.value == 'azure'",
                    awRequiredWhen: {
                        variable: 'subscription_required',
                        init: false
                    },
                    addRequired: false,
                    editRequired: false,
                    autocomplete: false,
                    awPopOver: '<p>Subscription ID is an Azure construct, which is mapped to a username.</p>',
                    dataTitle: 'Subscription ID',
                    dataPlacement: 'right',
                    dataContainer: "body"

                },
                "api_key": {
                    label: 'API Key',
                    type: 'sensitive',
                    ngShow: "kind.value == 'rax'",
                    awRequiredWhen: {
                        variable: "rackspace_required",
                        init: false
                    },
                    autocomplete: false,
                    ask: false,
                    hasShowInputButton: true,
                    clear: false,
                },
                "password": {
                    label: 'Password',
                    type: 'sensitive',
                    ngShow: "kind.value == 'scm' || kind.value == 'vmware'",
                    addRequired: false,
                    editRequired: false,
                    ask: false,
                    clear: false,
                    autocomplete: false,
                    hasShowInputButton: true,
                    awRequiredWhen: {
                        variable: "password_required",
                        init: false
                    }
                },
                "ssh_password": {
                    label: 'Password', // formally 'SSH Password'
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh'",
                    addRequired: false,
                    editRequired: false,
                    ask: true,
                    hasShowInputButton: true,
                    autocomplete: false
                },
                "ssh_key_data": {
                    labelBind: 'sshKeyDataLabel',
                    type: 'textarea',
                    ngShow: "kind.value == 'ssh' || kind.value == 'scm' || " +
                            "kind.value == 'gce' || kind.value == 'azure'",
                    awRequiredWhen: {
                        variable: 'key_required',
                        init: true
                    },
                    hintText: "{{ key_hint }}",
                    addRequired: false,
                    editRequired: false,
                    awDropFile: true,
                    'class': 'ssh-key-field',
                    rows: 10,
                    awPopOver: "SSH key description",
                    awPopOverWatch:   "key_description",
                    dataTitle: 'Help',
                    dataPlacement: 'right',
                    dataContainer: "body"
                },
                "ssh_key_unlock": {
                    label: 'Private Key Passphrase',
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh' || kind.value == 'scm'",
                    addRequired: false,
                    editRequired: false,
                    ask: true,
                    hasShowInputButton: true,
                    askShow: "kind.value == 'ssh'",  // Only allow ask for machine credentials
                },
                "login_method": {
                    label: "Privilege Escalation Credentials",
                    hintText: "If your playbooks use privilege escalation (\"sudo: true\", \"su: true\", etc), you can specify the username to become, and the password to use here.",
                    type: 'radio_group',
                    ngShow: "kind.value == 'ssh'",
                    ngChange: "loginMethodChange()",
                    options: [{
                        label: 'None', // FIXME: Maybe 'Default' or 'SSH only' instead?
                        value: '',
                        selected: true
                    }, {
                        label: 'Sudo',
                        value: 'sudo'
                    }, {
                        label: 'Su',
                        value: 'su'
                    },{
                        label: 'Pbrun',
                        value: 'pbrun'
                    }],
                    awPopOver: "<p><b>Sudo:</b> Optionally specify a username for sudo operations.  This is equivalent to specifying the <code>ansible-playbook --sudo-user</code> parameter.<br /><b>Su:</b> Optionally specify a username for su operations.  This is equivalent to specifying the <code>ansible-playbook --su-user</code> parameter.",
                    dataPlacement: 'right',
                    dataContainer: "body"
                },
                "sudo_username": {
                    label: 'Sudo Username',
                    type: 'text',
                    ngShow: "kind.value == 'ssh' && login_method == 'sudo'",
                    addRequired: false,
                    editRequired: false,
                    autocomplete: false
                },
                "sudo_password": {
                    label: 'Sudo Password',
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh' && login_method == 'sudo'",
                    addRequired: false,
                    editRequired: false,
                    ask: true,
                    hasShowInputButton: true,
                    autocomplete: false
                },
                "su_username": {
                    label: 'Su Username',
                    type: 'text',
                    ngShow: "kind.value == 'ssh' && login_method == 'su'",
                    addRequired: false,
                    editRequired: false,
                    autocomplete: false
                },
                "su_password": {
                    label: 'Su Password',
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh' && login_method == 'su'",
                    addRequired: false,
                    editRequired: false,
                    ask: true,
                    hasShowInputButton: true,
                    autocomplete: false
                },
                "pbrun_username": {
                    label: 'Pbrun Username',
                    type: 'text',
                    ngShow: "kind.value == 'ssh' && login_method == 'pbrun'",
                    addRequired: false,
                    editRequired: false,
                    autocomplete: false
                },
                "pbrun_password": {
                    label: 'Pbrun Password',
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh' && login_method == 'pbrun'",
                    addRequired: false,
                    editRequired: false,
                    ask: true,
                    hasShowInputButton: true,
                    autocomplete: false
                },
                "project": {
                    label: "Project",
                    type: 'text',
                    ngShow: "kind.value == 'gce'",
                    awRequiredWhen: {
                        variable: 'project_required',
                        init: false
                    },
                    awPopOver: "<p>The Project ID is the GCE assigned identification. It is constructed as two words followed by a three digit number.  Such as: </p><p>adjective-noun-000</p>",
                    dataTitle: 'Project ID',
                    dataPlacement: 'right',
                    dataContainer: "body",
                    addRequired: false,
                    editRequired: false,
                    autocomplete: false
                },
                "vault_password": {
                    label: "Vault Password",
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh'",
                    addRequired: false,
                    editRequired: false,
                    ask: true,
                    hasShowInputButton: true,
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
