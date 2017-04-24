/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:CredentialType
 * @description This form is for adding/editing a credential type
*/

export default ['i18n', function(i18n) {
    return {

        addTitle: i18n._('NEW CREDENTIAL TYPE'),
        editTitle: '{{ name }}',
        name: 'credential_type',
        basePath: 'credential_types',
        stateTree: 'credentialTypes',
        breadcrumbName: i18n._('CREDENTIAL TYPE'),
        showActions: true,

        // TODO: update fields to be the schema for credential types instead of inventory scripts
        fields: {
            name: {
                label: i18n._('Name'),
                type: 'text',
                ngDisabled: '!(credential_type.summary_fields.user_capabilities.edit || canAdd)',
                required: true,
                capitalize: false
            },
            description: {
                label: i18n._('Description'),
                type: 'text',
                ngDisabled: '!(credential_type.summary_fields.user_capabilities.edit || canAdd)'
            },
            kind: {
                label: i18n._('Kind'),
                excludeModal: true,
                type: 'select',
                ngOptions: 'kind.label for kind in credential_kind_options track by kind.value',
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
                        '<dt>' + i18n._('Cloud') + '</dt>\n' +
                        '<dd>' + i18n._('Usernames, passwords, and access keys for authenticating to the specified cloud or infrastructure ' +
                        'provider. These are used for dynamic inventory sources and for cloud provisioning and deployment ' +
                        'in playbook runs.') + '</dd>\n' +
                        '</dl>\n',
                dataTitle: i18n._('Kind'),
                dataPlacement: 'right',
                dataContainer: "body",
                ngDisabled: '!(credential_type.summary_fields.user_capabilities.edit || canAdd)'
            },
            inputs: {
                label: i18n._('Input Configuration'),
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                type: 'textarea',
                rows: 6,
                default: '---',
                showParseTypeToggle: true,
                parseTypeName: 'parseTypeInputs',
                awPopOver: '<p>TODO: input config helper text</p>',
                dataTitle: i18n._('Input Configuration'),
                dataPlacement: 'right',
                dataContainer: "body",
                ngDisabled: '!(credential_type.summary_fields.user_capabilities.edit || canAdd)'
            },
            injectors: {
                label: i18n._('Injector Configuration'),
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                type: 'textarea',
                rows: 6,
                default: '---',
                showParseTypeToggle: true,
                parseTypeName: 'parseTypeInjectors',
                awPopOver: '<p>TODO: injector config helper text</p>',
                dataTitle: i18n._('Injector Configuration'),
                dataPlacement: 'right',
                dataContainer: "body",
                ngDisabled: '!(credential_type.summary_fields.user_capabilities.edit || canAdd)'
            },
        },

        buttons: { //for now always generates <button> tags
            cancel: {
                ngClick: 'formCancel()',
                ngShow: '(credential_type.summary_fields.user_capabilities.edit || canAdd)'
            },
            close: {
                ngClick: 'formCancel()',
                ngShow: '!(credential_type.summary_fields.user_capabilities.edit || canAdd)'
            },
            save: {
                ngClick: 'formSave()', //$scope.function to call on click, optional
                ngDisabled: 'credential_type_form.$invalid', //Disable when $invalid, optional
                ngShow: '(credential_type.summary_fields.user_capabilities.edit || canAdd)'
            }
        }
    };
}];
