/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Organization.js
 *  Form definition for Organization model
 *
 *
 */
 /**
 * @ngdoc function
 * @name forms.function:Organizations
 * @description This form is for adding/editing an organization
*/
angular.module('CustomInventoryFormDefinition', [])
    .value('CustomInventoryForm', {

        addTitle: 'Create Custom Inventory', //Title in add mode
        editTitle: '{{ name }}', //Title in edit mode
        name: 'custom_inventory', //entity or model name in singular form
        well: false,
        showActions: false,

        fields: {
            name: {
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                capitalize: false
            },
            description: {
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false
            },
            organization: {
                label: 'Organization',
                type: 'lookup',
                awRequiredWhen: {
                    variable: "orgrequired",
                    init: true
                },
                sourceModel: 'organization',
                sourceField: 'name',
                ngClick: 'lookUpOrganization()'
            },
            script: {
                label: 'Custom Script',
                type: 'textarea',
                hintText: "Drag and drop an inventory script on the field below",
                addRequired: true,
                editRequired: true,
                awDropFile: true,
                'class': 'ssh-key-field',
                rows: 10,
                awPopOver: "<p>Drag and drop your custom inventory script file here or create one in the field to import your custom inventory. </p>",
                dataTitle: 'Custom Script',
                dataPlacement: 'right',
                dataContainer: "body"
            },
        },

        buttons: { //for now always generates <button> tags
            save: {
                ngClick: 'formSave()', //$scope.function to call on click, optional
                ngDisabled: true //Disable when $pristine or $invalid, optional
            },
            reset: {
                ngClick: 'formReset()',
                ngDisabled: true //Disabled when $pristine
            }
        },



    }); //OrganizationForm
