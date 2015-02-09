/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  License.js
 *  Form definition for Organization model
 *
 *
 */
 /**
 * @ngdoc function
 * @name forms.function:LicenseUpdate
 * @description This form is for updating a license
*/

export default
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
                },
                eula: {
                    label: 'End User License Agreement',
                    type: 'textarea',
                    addRequired: true,
                    editRequird: true,
                    rows: 5,
                    readonly: true
                },
                eula_agreement: {
                    label: 'I agree to the End User License Agreement',
                    type: 'checkbox',
                    addRequired: true,
                    editRequird: true
                }
            },
            buttons: {
                form_submit: {
                    label: "Submit",
                    "class": "pull-right btn-primary",
                    ngClick: "submitLicenseKey()",
                    // ngDisabled:  "true"
                }
            },

            related: { }

        }); //LicenseUpdateForm
