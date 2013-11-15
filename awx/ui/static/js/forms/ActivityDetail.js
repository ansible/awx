/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
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

        fields: {
            timestamp: {
                label: 'Time',
                type: 'text',
                readonly: true
                },
            operation: {
                label: 'Operation',
                type: 'text',
                readonly: true
                },
            object1: {
                label: 'Object 1',
                type: 'text',
                ngHide: '!object1',
                readonly: true
                },
            object1_name: {
                label: 'Name',
                type: 'text',
                ngHide: '!object1',
                readonly: true
                },
            object2: {
                label: 'Object 2',
                type: 'text',
                ngHide: '!object2',
                readonly: true
                },
            object2_name: {
                label: 'Name',
                type: 'text',
                ngHide: '!object2',
                readonly: true
                },
            changes: {
                label: 'Changes',
                type: 'textarea',
                readonly: true
                }
            }        
    
    }); //Form
