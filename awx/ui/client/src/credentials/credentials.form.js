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

export default ['i18n', function(i18n) {
        return {

            addTitle: i18n._('CREATE CREDENTIAL'), //Legend in add mode
            editTitle: '{{ name }}', //Legend in edit mode
            name: 'credential',
            // the top-most node of generated state tree
            stateTree: 'credentials',
            forceListeners: true,
            subFormTitles: {
                credentialSubForm: i18n._('Type Details'),
            },

            actions: {

            },

            fields: {
                name: {
                    label: i18n._('Name'),
                    type: 'text',
                    required: true,
                    autocomplete: false,
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                description: {
                    label: i18n._('Description'),
                    type: 'text',
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                organization: {
                    basePath: 'organizations',
                    ngShow: 'canShareCredential',
                    label: i18n._('Organization'),
                    type: 'lookup',
                    autopopulateLookup: false,
                    list: 'OrganizationList',
                    sourceModel: 'organization',
                    sourceField: 'name',
                    awPopOver: "<p>" + i18n._("If no organization is given, the credential can only be used by the user that creates the credential.  Organization admins and system administrators can assign an organization so that roles for the credential can be assigned to users and teams in that organization.") + "</p>",
                    dataTitle: i18n._('Organization') + ' ',
                    dataPlacement: 'bottom',
                    dataContainer: "body",
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd) || !canEditOrg',
                    awLookupWhen: '(credential_obj.summary_fields.user_capabilities.edit || canAdd) && canEditOrg'
                },
                kind: {
                    label: i18n._('Type'),
                    excludeModal: true,
                    type: 'select',
                    ngOptions: 'kind.label for kind in credential_kind_options track by kind.value', //  select as label for value in array 'kind.label for kind in credential_kind_options',
                    ngChange: 'kindChange()',
                    required: true,
                    awPopOver: '<dl>\n' +
                            '<dt>' + i18n._('Machine') + '</dt>\n' +
                            '<dd>' + i18n._('Authentication for remote machine access. This can include SSH keys, usernames, passwords, ' +
                            'and sudo information. Machine credentials are used when submitting jobs to run playbooks against ' +
                            'remote hosts.') + '</dd>' +
                            '<dt>' + i18n._('Network') + '</dt>\n' +
                            '<dd>' + i18n._('Authentication for network device access. This can include SSH keys, usernames, passwords, ' +
                            'and authorize information. Network credentials are used when submitting jobs to run playbooks against ' +
                            'network devices.') + '</dd>' +
                            '<dt>' + i18n._('Source Control') + '</dt>\n' +
                            '<dd>' + i18n._('Used to check out and synchronize playbook repositories with a remote source control ' +
                            'management system such as Git, Subversion (svn), or Mercurial (hg). These credentials are ' +
                            'used by Projects.') + '</dd>\n' +
                            '<dt>' + i18n._('Others (Cloud Providers)') + '</dt>\n' +
                            '<dd>' + i18n._('Usernames, passwords, and access keys for authenticating to the specified cloud or infrastructure ' +
                            'provider. These are used for smart inventory sources and for cloud provisioning and deployment ' +
                            'in playbook runs.') + '</dd>\n' +
                            '</dl>\n',
                    dataTitle: i18n._('Type'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    hasSubForm: true,
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                access_key: {
                    label: i18n._('Access Key'),
                    type: 'text',
                    ngShow: "kind.value == 'aws'",
                    awRequiredWhen: {
                        reqExpression: "aws_required",
                        init: false
                    },
                    autocomplete: false,
                    apiField: 'username',
                    subForm: 'credentialSubForm',
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                secret_key: {
                    label: i18n._('Secret Key'),
                    type: 'sensitive',
                    ngShow: "kind.value == 'aws'",
                    ngDisabled: "secret_key_ask || !(credential_obj.summary_fields.user_capabilities.edit || canAdd)",
                    awRequiredWhen: {
                        reqExpression: "aws_required",
                        init: false
                    },
                    autocomplete: false,
                    clear: false,
                    hasShowInputButton: true,
                    apiField: 'password',
                    subForm: 'credentialSubForm'
                },
                security_token: {
                    label: i18n._('STS Token'),
                    type: 'sensitive',
                    ngShow: "kind.value == 'aws'",
                    autocomplete: false,
                    apiField: 'security_token',
                    awPopOver: "<div>" + i18n._("Security Token Service (STS) is a web service that enables you to request temporary, limited-privilege credentials for AWS Identity and Access Management (IAM) users.") + "</div><div style='padding-top: 10px'>" +
                               i18n.sprintf(i18n._("To learn more about the IAM STS Token, refer to the %sAmazon documentation%s."), "<a href='http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html' target='_blank'>", "</a>") + "</div>",
                    hasShowInputButton: true,
                    dataTitle: i18n._('STS Token'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subForm: 'credentialSubForm',
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                "host": {
                    labelBind: 'hostLabel',
                    type: 'text',
                    ngShow: "kind.value == 'vmware' || kind.value == 'openstack' || kind.value === 'satellite6' || kind.value === 'cloudforms'",
                    awPopOverWatch: "hostPopOver",
                    awPopOver: i18n._("set in helpers/credentials"),
                    dataTitle: i18n._('Host'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    autocomplete: false,
                    awRequiredWhen: {
                        reqExpression: 'host_required',
                        init: false
                    },
                    subForm: 'credentialSubForm',
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                "subscription": {
                    label: i18n._("Subscription ID"),
                    type: 'text',
                    ngShow: "kind.value == 'azure_rm'",
                    awRequiredWhen: {
                        reqExpression: 'subscription_required',
                        init: false
                    },


                    autocomplete: false,
                    awPopOver: '<p>' + i18n._('Subscription ID is an Azure construct, which is mapped to a username.') + '</p>',
                    dataTitle: i18n._('Subscription ID'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subForm: 'credentialSubForm',
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                "username": {
                    labelBind: 'usernameLabel',
                    type: 'text',
                    ngShow: "kind.value && kind.value !== 'aws' && " +
                            "kind.value !== 'gce'",
                    awRequiredWhen: {
                        reqExpression: 'username_required',
                        init: false
                    },
                    autocomplete: false,
                    subForm: "credentialSubForm",
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                "email_address": {
                    labelBind: 'usernameLabel',
                    type: 'email',
                    ngShow: "kind.value === 'gce'",
                    awRequiredWhen: {
                        reqExpression: 'email_required',
                        init: false
                    },
                    autocomplete: false,
                    awPopOver: '<p>' + i18n.sprintf(i18n._('The email address assigned to the Google Compute Engine %sservice account.'), '<b><i>') + '</b></i></p>',
                    dataTitle: i18n._('Email'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subForm: 'credentialSubForm',
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                "api_key": {
                    label: i18n._('API Key'),
                    type: 'sensitive',
                    ngShow: "kind.value == 'rax'",
                    awRequiredWhen: {
                        reqExpression: "rackspace_required",
                        init: false
                    },
                    autocomplete: false,
                    hasShowInputButton: true,
                    clear: false,
                    subForm: 'credentialSubForm',
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                "password": {
                    labelBind: 'passwordLabel',
                    type: 'sensitive',
                    ngShow: "kind.value == 'scm' || kind.value == 'vmware' || kind.value == 'openstack'|| kind.value == 'satellite6'|| kind.value == 'cloudforms'|| kind.value == 'net' || kind.value == 'azure_rm'",
                    clear: false,
                    autocomplete: false,
                    hasShowInputButton: true,
                    awRequiredWhen: {
                        reqExpression: "password_required",
                        init: false
                    },
                    subForm: "credentialSubForm",
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                "ssh_password": {
                    label: i18n._('Password'),
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh'",
                    ngDisabled: "ssh_password_ask || !(credential_obj.summary_fields.user_capabilities.edit || canAdd)",
                    subCheckbox: {
                        variable: 'ssh_password_ask',
                        text: i18n._('Ask at runtime?'),
                        ngChange: 'ask(\'ssh_password\', \'undefined\')',
                        ngDisabled: false,
                    },
                    hasShowInputButton: true,
                    autocomplete: false,
                    subForm: 'credentialSubForm'
                },
                "ssh_key_data": {
                    labelBind: 'sshKeyDataLabel',
                    type: 'textarea',
                    ngShow: "kind.value == 'ssh' || kind.value == 'scm' || " +
                            "kind.value == 'gce' || kind.value == 'net'",
                    awRequiredWhen: {
                        reqExpression: 'key_required',
                        init: true
                    },
                    class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                    elementClass: 'Form-monospace',


                    awDropFile: true,
                    rows: 10,
                    awPopOver: i18n._("SSH key description"),
                    awPopOverWatch:   "key_description",
                    dataTitle: i18n._('Private Key'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subForm: "credentialSubForm",
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                "ssh_key_unlock": {
                    label: i18n._('Private Key Passphrase'),
                    type: 'sensitive',
                    ngShow: "kind.value === 'ssh' || kind.value === 'scm' || kind.value === 'net'",
                    ngDisabled: "keyEntered === false || ssh_key_unlock_ask || !(credential_obj.summary_fields.user_capabilities.edit || canAdd)",
                    subCheckbox: {
                        variable: 'ssh_key_unlock_ask',
                        ngShow: "kind.value == 'ssh'",
                        text: i18n._('Ask at runtime?'),
                        ngChange: 'ask(\'ssh_key_unlock\', \'undefined\')',
                        ngDisabled: "keyEntered === false"
                    },
                    hasShowInputButton: true,
                    subForm: 'credentialSubForm'
                },
                "become_method": {
                    label: i18n._("Privilege Escalation"),
                    // hintText: "If your playbooks use privilege escalation (\"sudo: true\", \"su: true\", etc), you can specify the username to become, and the password to use here.",
                    type: 'text',
                    ngShow: "kind.value == 'ssh'",
                    dataTitle: i18n._('Privilege Escalation'),
                    awPopOver: "<p>" + i18n.sprintf(i18n._("Specify a method for %s operations. " +
                    "This is equivalent to specifying the %s parameter, where %s could be "+
                    "%s"), "'become'", "<code>--become-method=BECOME_METHOD</code>", "<code>BECOME_METHOD</code>", "<code>sudo | su | pbrun | pfexec | runas</code>") + " <br>" + i18n.sprintf(i18n._("(defaults to %s)"), "<code>sudo</code>") + "</p>",
                    dataPlacement: 'right',
                    dataContainer: "body",
                    subForm: 'credentialSubForm',
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)',
                    ngChange: 'becomeMethodChange()',
                },
                "become_username": {
                    label: i18n._('Privilege Escalation Username'),
                    type: 'text',
                    ngShow: "(kind.value == 'ssh' && (become_method && become_method.value)) ",


                    autocomplete: false,
                    subForm: 'credentialSubForm',
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                "become_password": {
                    label: i18n._('Privilege Escalation Password'),
                    type: 'sensitive',
                    ngShow: "(kind.value == 'ssh' && (become_method && become_method.value)) ",
                    ngDisabled: "become_password_ask || !(credential_obj.summary_fields.user_capabilities.edit || canAdd)",
                    subCheckbox: {
                        variable: 'become_password_ask',
                        text: i18n._('Ask at runtime?'),
                        ngChange: 'ask(\'become_password\', \'undefined\')',
                        ngDisabled: false,
                    },
                    hasShowInputButton: true,
                    autocomplete: false,
                    subForm: 'credentialSubForm'
                },
                client:{
                    type: 'text',
                    label: i18n._('Client ID'),
                    subForm: 'credentialSubForm',
                    ngShow: "kind.value === 'azure_rm'",
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                secret:{
                    type: 'sensitive',
                    hasShowInputButton: true,
                    autocomplete: false,
                    label: i18n._('Client Secret'),
                    subForm: 'credentialSubForm',
                    ngShow: "kind.value === 'azure_rm'",
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                tenant: {
                    type: 'text',
                    label: i18n._('Tenant ID'),
                    subForm: 'credentialSubForm',
                    ngShow: "kind.value === 'azure_rm'",
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                authorize: {
                    label: i18n._('Authorize'),
                    type: 'checkbox',
                    ngChange: "toggleCallback('host_config_key')",
                    subForm: 'credentialSubForm',
                    ngShow: "kind.value === 'net'",
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                authorize_password: {
                    label: i18n._('Authorize Password'),
                    type: 'sensitive',
                    hasShowInputButton: true,
                    autocomplete: false,
                    subForm: 'credentialSubForm',
                    ngShow: "authorize && authorize !== 'false'",
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                "project": {
                    labelBind: 'projectLabel',
                    type: 'text',
                    ngShow: "kind.value == 'gce' || kind.value == 'openstack'",
                    awPopOverWatch: "projectPopOver",
                    awPopOver: i18n._("set in helpers/credentials"),
                    dataTitle: i18n._('Project Name'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    awRequiredWhen: {
                        reqExpression: 'project_required',
                        init: false
                    },
                    subForm: 'credentialSubForm',
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                "domain": {
                    labelBind: 'domainLabel',
                    type: 'text',
                    ngShow: "kind.value == 'openstack'",
                    awPopOver: "<p>" + i18n._("OpenStack domains define administrative " +
                    "boundaries. It is only needed for Keystone v3 authentication URLs. " +
                    "Common scenarios include:") + "<ul><li><b>" + i18n.sprintf(i18n._("v2 URLs%s - leave blank"), "</b>") + "</li>" +
                    "<li><b>" + i18n.sprintf(i18n._("v3 default%s - set to 'default'"), "</b>") + "</br></li>" +
                    "<li><b>" + i18n.sprintf(i18n._("v3 multi-domain%s - your domain name"), "</b>") + "</p></li></ul></p>",
                    dataTitle: i18n._('Domain Name'),
                    dataPlacement: 'right',
                    dataContainer: "body",
                    ngDisabled: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)',
                    subForm: 'credentialSubForm'
                },
                "vault_password": {
                    label: i18n._("Vault Password"),
                    type: 'sensitive',
                    ngShow: "kind.value == 'ssh'",
                    ngDisabled: "vault_password_ask || !(credential_obj.summary_fields.user_capabilities.edit || canAdd)",
                    subCheckbox: {
                        variable: 'vault_password_ask',
                        text: i18n._('Ask at runtime?'),
                        ngChange: 'ask(\'vault_password\', \'undefined\')',
                        ngDisabled: false,
                    },
                    hasShowInputButton: true,
                    autocomplete: false,
                    subForm: 'credentialSubForm'
                }
            },

            buttons: {
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: '(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                save: {
                    label: i18n._('Save'),
                    ngClick: 'formSave()', //$scope.function to call on click, optional
                    ngDisabled: true,
                    ngShow: '(credential_obj.summary_fields.user_capabilities.edit || canAdd)' //Disable when $pristine or $invalid, optional
                }
            },

            related: {
                permissions: {
                    name: 'permissions',
                    disabled: '(organization === undefined ? true : false)',
                    // Do not transition the state if organization is undefined
                    ngClick: `(organization === undefined ? true : false)||$state.go('credentials.edit.permissions')`,
                    awToolTip: '{{permissionsTooltip}}',
                    dataTipWatch: 'permissionsTooltip',
                    awToolTipTabEnabledInEditMode: true,
                    dataPlacement: 'right',
                    basePath: 'api/v2/credentials/{{$stateParams.credential_id}}/access_list/',
                    search: {
                        order_by: 'username'
                    },
                    type: 'collection',
                    title: i18n._('Permissions'),
                    iterator: 'permission',
                    index: false,
                    open: false,
                    actions: {
                        add: {
                            mode: 'all',
                            ngClick: "$state.go('.add')",
                            label: i18n._('Add'),
                            awToolTip: i18n._('Add a permission'),
                            actionClass: 'at-Button--add',
                            actionId: 'button-add--permission',
                            ngShow: '(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                        }
                    },
                    fields: {
                        username: {
                            key: true,
                            label: i18n._('User'),
                            linkBase: 'users',
                            columnClass: 'col-sm-3 col-xs-4'
                        },
                        role: {
                            label: i18n._('Role'),
                            type: 'role',
                            nosort: true,
                            columnClass: 'col-sm-4 col-xs-4'
                        },
                        team_roles: {
                            label: i18n._('Team Roles'),
                            type: 'team_roles',
                            nosort: true,
                            columnClass: 'col-sm-5 col-xs-4'
                        }
                    }
                }
            }
        };}];
