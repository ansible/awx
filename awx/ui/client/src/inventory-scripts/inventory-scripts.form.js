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
        name: 'inventory_script',
        basePath: 'inventory_scripts',
        stateTree: 'inventoryScripts',
        showActions: true,

        fields: {
            name: {
                label: i18n._('Name'),
                type: 'text',
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || !canAdd)',
                required: true,
                capitalize: false
            },
            description: {
                label: i18n._('Description'),
                type: 'text',
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || !canAdd)'
            },
            organization: {
                label: i18n._('Organization'),
                type: 'lookup',
                list: 'OrganizationList',
                basePath: 'organizations',
                awRequiredWhen: {
                    reqExpression: "orgrequired",
                    init: true
                },
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || !canAdd)'
            },
            script: {
                label: i18n._('Custom Script'),
                type: 'textarea',
                class: 'Form-formGroup--fullWidth',
                elementClass: 'Form-monospace',
                required: true,
                awDropFile: true,
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || !canAdd)',
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
                ngShow: '(inventory_script_obj.summary_fields.user_capabilities.edit || !canAdd)'
            },
            close: {
                ngClick: 'formCancel()',
                ngShow: '!(inventory_script_obj.summary_fields.user_capabilities.edit || !canAdd)'
            },
            save: {
                ngClick: 'formSave()', //$scope.function to call on click, optional
                ngDisabled: 'inventory_script_form.$pristine || inventory_script_form.$invalid', //Disable when $pristine or $invalid, optional
                ngShow: '(inventory_script_obj.summary_fields.user_capabilities.edit || !canAdd)'
            }
        }
    };
}];
