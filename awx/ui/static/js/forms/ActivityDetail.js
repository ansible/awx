/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  ActivityDetail.js
 *  Form definition for Activity Stream detail
 *  
 */
angular.module('ActivityDetailDefinition', [])
    .value(
    'ActivityDetailForm', {
    
        name: 'activity',
        editTitle: 'Activity Detail', 
        well: false,
        'class': 'horizontal-narrow',
        formFieldSize: 'col-lg-10',
        formLabelSize: 'col-lg-2',

        fields: {
            user: {
                label: "Initiated by",
                type: 'text',
                readonly: true
                },
            operation: {
                label: 'Operation',
                type: 'text',
                readonly: true
                },
            /*object1_name: {
                label: '\{\{ object1 \}\}',
                type: 'text',
                ngHide: '!object1',
                readonly: true
                },
            object2_name: {
                label: '\{\{ object2 \}\}',
                type: 'text',
                ngHide: '!object2',
                readonly: true
                },*/
            changes: {
                label: 'Changes',
                type: 'textarea',
                ngHide: "!changes || changes =='' || changes == 'null'",
                readonly: true
                }
            }        
    
    }); //Form
