/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:CustomInventory
 * @description This form is for adding/editing an organization
*/

export default ['i18n', function(i18n) {
    return {

        addTitle: i18n._('New Custom Inventory'),
        editTitle: '{{ name }}',
        name: 'custom_inventory',
        showActions: true,

        fields: {
            name: {
                label: i18n._('Name'),
                type: 'text',
                addRequired: true,
                editRequired: true,
                capitalize: false,
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            description: {
                label: i18n._('Description'),
                type: 'text',
                addRequired: false,
                editRequired: false,
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            organization: {
                label: i18n._('Organization'),
                type: 'lookup',
                awRequiredWhen: {
                    reqExpression: "orgrequired",
                    init: true
                },
                sourceModel: 'organization',
                sourceField: 'name',
                ngClick: 'lookUpOrganization()',
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            script: {
                label: i18n._('Custom Script'),
                type: 'textarea',
                class: 'Form-formGroup--fullWidth',
                elementClass: 'Form-monospace',
                addRequired: true,
                editRequired: true,
                awDropFile: true,
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)',
                rows: 10,
                awPopOver: i18n._("<p>Drag and drop your custom inventory script file here or create one in the field to import your custom inventory. " +
                                    "<br><br> Script must begin with a hashbang sequence: i.e.... #!/usr/bin/env python</p>"),
                dataTitle: i18n._('Custom Script'),
                dataPlacement: 'right',
                dataContainer: "body"
            },
        },

        buttons: { //for now always generates <button> tags
            cancel: {
                ngClick: 'formCancel()',
                ngShow: '(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            close: {
                ngClick: 'formCancel()',
                ngShow: '!(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            save: {
                ngClick: 'formSave()', //$scope.function to call on click, optional
                ngDisabled: 'custom_inventory_form.$pristine || custom_inventory_form.$invalid', //Disable when $pristine or $invalid, optional
                ngShow: '(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)'
            }
        }
    };
}];
