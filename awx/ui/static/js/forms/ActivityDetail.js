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
            timestamp: {
                label: 'Time',
                type: 'text',
                readonly: true
                },
            user: {
                label: 'Initiated By',
                type: 'text',
                readonly: true
                },
            id: {
                label: 'Event ID', 
                type: 'text',
                readonly: true
                },
            operation: {
                label: 'Operation',
                type: 'text',
                readonly: true
                },
            object1: {
                label: 'Resource',
                type: 'text',
                ngHide: '!object1',
                readonly: true
                },
            object1_name: {
                label: 'Name',
                type: 'text',
                ngHide: '!object1_name',
                readonly: true
                },
            object2: {
                label: 'Related',
                type: 'text',
                ngHide: '!object2',
                readonly: true
                },
            object2_name: {
                label: 'Name',
                type: 'text',
                ngHide: '!object2_name',
                readonly: true
                },
            changes: {
                label: 'Changes',
                type: 'textarea',
                ngHide: "!changes || changes =='' || changes == 'null'",
                readonly: true
                }
            }        
    
    }); //Form
