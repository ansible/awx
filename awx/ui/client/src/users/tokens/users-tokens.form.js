/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:Tokens
 * @description This form is for adding a token on the user's page
*/

export default ['i18n',
function(i18n) {
        return {
            addTitle: i18n._('CREATE TOKEN'),
            name: 'token',
            basePath: 'tokens',
            well: false,
            formLabelSize: 'col-lg-3',
            formFieldSize: 'col-lg-9',
            iterator: 'token',
            stateTree: 'users',
            fields: {
                application: {
                    label: i18n._('Application'),
                    type: 'lookup',
                    list: 'ApplicationList',
                    sourceModel: 'application',
                    // TODO: update to actual path
                    basePath: 'projects',
                    sourceField: 'name',
                    dataTitle: i18n._('Application'),
                    required: true,
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    ngDisabled: '!(token.summary_fields.user_capabilities.edit || canAdd)',
                    awLookupWhen: '(token.summary_fields.user_capabilities.edit || canAdd)'
                    // TODO: help popover
                },
                scope: {
                    label: i18n._('Description'),
                    type: 'select',
                    class: 'Form-dropDown--scmType',
                    defaultText: 'Choose a scope',
                    ngOptions: 'scope.label for scope in scope_options track by scope.value',
                    required: true,
                    ngDisabled: '!(token.summary_fields.user_capabilities.edit || canAdd)'
                    // TODO: help popover
                }
            },
            buttons: {
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: '(token.summary_fields.user_capabilities.edit || canAdd)'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!(token.summary_fields.user_capabilities.edit || canAdd)'
                },
                save: {
                    ngClick: 'formSave()',
                    ngDisabled: true,
                    ngShow: '(token.summary_fields.user_capabilities.edit || canAdd)'
                }
            },
            related: {
            }
        };
    }];
