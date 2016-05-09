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

export default function() {
    return {

        addTitle: 'New Custom Inventory',
        editTitle: '{{ name }}',
        name: 'custom_inventory',
        showActions: true,

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
                    reqExpression: "orgrequired",
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
                class: 'Form-formGroup--fullWidth',
                addRequired: true,
                editRequired: true,
                awDropFile: true,
                rows: 10,
                awPopOver: "<p>Drag and drop your custom inventory script file here or create one in the field to import your custom inventory. " +
                                    "<br><br> Script must begin with a hashbang sequence: i.e.... #!/usr/bin/env python</p>",
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
            cancel: {
                ngClick: 'formCancel()',
            }
        }
    };
}
