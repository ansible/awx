/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc overview
 * @name forms
 * @description These are all the controllers that are used throughout the application
 *
*/
/**
 * @ngdoc function
 * @name forms.function:ActivityDetail
 * @description This form is for activity detail modal that can be shown on most pages.
*/

export default ['i18n', function(i18n) {
        return {

            name: 'activity',
            editTitle: i18n._('ACTIVITY DETAIL'),
            well: false,
            'class': 'horizontal-narrow',
            formFieldSize: 'col-lg-10',
            formLabelSize: 'col-lg-2',

            fields: {
                user: {
                    label: i18n._("Initiated by"),
                    type: 'text',
                    readonly: true
                },
                operation: {
                    label: i18n._('Action'),
                    type: 'text',
                    readonly: true
                },
                changes: {
                    label: i18n._('Changes'),
                    type: 'textarea',
                    class: 'Form-textAreaLabel',
                    ngHide: "!changes || changes =='' || changes == 'null'",
                    readonly: true
                }
            }

        };}];
