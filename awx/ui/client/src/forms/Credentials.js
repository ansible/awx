/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

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
            forceListeners: true,
            subFormTitles: {
                credentialSubForm: 'Type Details',
            },

            actions: {

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
                organization: {
                    addRequired: false,
                    editRequired: false,
                    ngShow: 'canShareCredential',
                    label: 'Organization',
                    type: 'lookup',
                    sourceModel: 'organization',
                    sourceField: 'name',
                    ngClick: 'lookUpOrganization()',
                    awPopOver: "<p>If no organization is given, the credential can only be used by the user that creates the credential.  organization admins and system administrators can assign an organization so that roles can be assigned to users and teams in that organization.</p>",
                    dataTitle: 'Required ',
                    dataPlacement: 'bottom',
                    dataContainer: "body"
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
                    dataContainer: "body",
                    hasSubForm: true,
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
                    apiField: 'username',
                    subForm: 'credentialSubForm',
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
                    apiField: 'passwowrd',
                    subForm: 'credentialSubForm'
                },
                security_token: {
                    label: 'STS Token',
                    type: 'sensitive',
                    ngShow: "kind.value == 'aws'",
                    autocomplete: false,
                    apiField: 'security_token',
                    awPopOver: "<div>Security Token Service (STS) is a web service that enables you to request temporary, limited-privilege credentials for AWS Identity and Access Management (IAM) users.</div><div style='padding-top: 10px'>To learn more about the IAM STS Token, refer to the <a href='http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html' target='_blank'>Amazon documentation</a>.</div>",
                    hasShowInputButton: true,
                    dataTitle: 'STS Token',
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subForm: 'credentialSubForm'
                },
                "host": {
                    labelBind: 'hostLabel',
                    type: 'text',
                    ngShow: "kind.value == 'vmware' || kind.value == 'openstack'",
                    awPopOverWatch: "hostPopOver",
                    awPopOver: "set in helpers/credentials",
                    dataTitle: 'Host',
                    dataPlacement: 'right',
                    dataContainer: "body",
                    autocomplete: false,
                    awRequiredWhen: {
                        variable: 'host_required',
                        init: false
                    },
                    subForm: 'credentialSubForm'
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
                    autocomplete: false,
                    subForm: "credentialSubForm"
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
                    dataContainer: "body",
                    subForm: 'credentialSubForm'
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
                    dataContainer: "body",
                    subForm: 'credentialSubForm'
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
                    subForm: 'credentialSubForm'
                },
                "password": {
                    labelBind: 'passwordLabel',
                    type: 'sensitive',
                    ngShow: "kind.value == 'scm' || kind.value == 'vmware' || kind.value == 'openstack'",
                    addRequired: false,
                    editRequired: false,
                    ask: false,
                    clear: false,
                    autocomplete: false,
                    hasShowInputButton: true,
                    awRequiredWhen: {
                        variable: "password_required",
                        init: false
                    },
                    subForm: "credentialSubForm"
                },
                "ssh_password": {
                    label: 'Password', // formally 'SSH Password'
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh'",
                    addRequired: false,
                    editRequired: false,
                    ask: true,
                    hasShowInputButton: true,
                    autocomplete: false,
                    subForm: 'credentialSubForm'
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
                    class: 'Form-textAreaLabel',
                    hintText: "{{ key_hint }}",
                    addRequired: false,
                    editRequired: false,
                    awDropFile: true,
                    rows: 10,
                    awPopOver: "SSH key description",
                    awPopOverWatch:   "key_description",
                    dataTitle: 'Help',
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subForm: "credentialSubForm"
                },
                "ssh_key_unlock": {
                    label: 'Private Key Passphrase',
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh' || kind.value == 'scm'",
                    addRequired: false,
                    editRequired: false,
                    ngDisabled: "keyEntered === false",
                    ask: true,
                    hasShowInputButton: true,
                    askShow: "kind.value == 'ssh'",  // Only allow ask for machine credentials
                    subForm: 'credentialSubForm'
                },
                "become_method": {
                    label: "Privilege Escalation",
                    // hintText: "If your playbooks use privilege escalation (\"sudo: true\", \"su: true\", etc), you can specify the username to become, and the password to use here.",
                    type: 'select',
                    ngShow: "kind.value == 'ssh'",
                    dataTitle: 'Privilege Escalation',
                    ngOptions: 'become.label for become in become_options track by become.value',
                    awPopOver: "<p>Specify a method for 'become' operations. " +
                    "This is equivalent to specifying the <code>--become-method=BECOME_METHOD</code> parameter, where <code>BECOME_METHOD</code> could be "+
                    "<code>sudo | su | pbrun | pfexec | runas</code> <br>(defaults to <code>sudo</code>)</p>",
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subForm: 'credentialSubForm'
                },
                "become_username": {
                    label: 'Privilege Escalation Username',
                    type: 'text',
                    ngShow: "kind.value == 'ssh' && (become_method && become_method.value)",
                    addRequired: false,
                    editRequired: false,
                    autocomplete: false,
                    subForm: 'credentialSubForm'
                },
                "become_password": {
                    label: 'Privilege Escalation Password',
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh' && (become_method && become_method.value)",
                    addRequired: false,
                    editRequired: false,
                    ask: true,
                    hasShowInputButton: true,
                    autocomplete: false,
                    subForm: 'credentialSubForm'
                },
                "project": {
                    labelBind: 'projectLabel',
                    type: 'text',
                    ngShow: "kind.value == 'gce' || kind.value == 'openstack'",
                    awPopOverWatch: "projectPopOver",
                    awPopOver: "set in helpers/credentials",
                    dataTitle: 'Project Name',
                    dataPlacement: 'right',
                    dataContainer: "body",
                    addRequired: false,
                    editRequired: false,
                    awRequiredWhen: {
                        variable: 'project_required',
                        init: false
                    },
                    subForm: 'credentialSubForm'
                },
                "domain": {
                    labelBind: 'domainLabel',
                    type: 'text',
                    ngShow: "kind.value == 'openstack'",
                    awPopOver: "<p>OpenStack domains define administrative " +
                    "boundaries. It is only needed for Keystone v3 authentication URLs. " +
                    "Common scenarios include:<ul><li><b>v2 URLs</b> - leave blank</li>" +
                    "<li><b>v3 default</b> - set to 'default'</br></li>" +
                    "<li><b>v3 multi-domain</b> - your domain name</p></li></ul></p>",
                    dataTitle: 'Domain Name',
                    dataPlacement: 'right',
                    dataContainer: "body",
                    addRequired: false,
                    editRequired: false,
                    subForm: 'credentialSubForm'
                },
                "vault_password": {
                    label: "Vault Password",
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh'",
                    addRequired: false,
                    editRequired: false,
                    ask: true,
                    hasShowInputButton: true,
                    autocomplete: false,
                    subForm: 'credentialSubForm'
                }
            },

            buttons: {
                save: {
                    label: 'Save',
                    ngClick: 'formSave()', //$scope.function to call on click, optional
                    ngDisabled: true //Disable when $pristine or $invalid, optional
                },
                cancel: {
                    ngClick: 'formCancel()',
                }
            },

            related: {}

        });
