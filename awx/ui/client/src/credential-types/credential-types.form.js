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
            inputs: {
                label: i18n._('Input Configuration'),
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                type: 'textarea',
                rows: 6,
                default: '---',
                showParseTypeToggle: true,
                parseTypeName: 'parseTypeInputs',
                awPopOver: i18n._("Enter inputs using either JSON or YAML syntax. Use the radio button to toggle between the two. Refer to the Ansible Tower documentation for example syntax."),
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
                awPopOver: i18n._("Enter injectors using either JSON or YAML syntax. Use the radio button to toggle between the two. Refer to the Ansible Tower documentation for example syntax."),
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
