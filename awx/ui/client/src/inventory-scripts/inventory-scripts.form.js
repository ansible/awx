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

        addTitle: i18n._('NEW CUSTOM INVENTORY'),
        editTitle: '{{ name }}',
        name: 'inventory_script',
        basePath: 'inventory_scripts',
        stateTree: 'inventoryScripts',
        // I18N for "CREATE INVENTORY_SCRIPT"
        // on /#/inventory_scripts/add
        breadcrumbName: i18n._('INVENTORY SCRIPT'),
        showActions: true,

        fields: {
            name: {
                label: i18n._('Name'),
                type: 'text',
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)',
                required: true,
                capitalize: false
            },
            description: {
                label: i18n._('Description'),
                type: 'text',
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            organization: {
                label: i18n._('Organization'),
                type: 'lookup',
                list: 'OrganizationList',
                basePath: 'organizations',
                required: true,
                sourceModel: 'organization',
                sourceField: 'name',
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            script: {
                label: i18n._('Custom Script'),
                type: 'textarea',
                class: 'Form-formGroup--fullWidth',
                elementClass: 'Form-monospace',
                required: true,
                awDropFile: true,
                ngDisabled: '!(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)',
                ngTrim: false,
                rows: 10,
                awPopOver: i18n._('Drag and drop your custom inventory script file here or create one in the field to import your custom inventory. Refer to the Ansible Tower documentation for example syntax.'),
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
                ngDisabled: 'inventory_script_form.$invalid', //Disable when $invalid, optional
                ngShow: '(inventory_script_obj.summary_fields.user_capabilities.edit || canAdd)'
            }
        }
    };
}];
