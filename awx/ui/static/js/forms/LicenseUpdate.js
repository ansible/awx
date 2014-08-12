/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  License.js
 *  Form definition for Organization model
 *
 *
 */
angular.module('LicenseUpdateFormDefinition', [])
    .value('LicenseUpdateForm', {

        name: 'license',
        well: false,

        fields: {
            license_json: {
                label: 'License File',
                type: 'textarea',
                addRequired: true,
                editRequird: true,
                rows: 10,
                'default': '---'
            }
        },

        buttons: {
            form_submit: {
                label: "Submit",
                "class": "pull-right btn-primary",
                ngClick: "submitLicenseKey()",
                ngDisabled: true
            }
        },

        related: { }

    }); //LicenseUpdateForm
