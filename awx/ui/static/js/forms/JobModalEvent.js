/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  JobModalEvent.js
 *  Form definition for Job Events model
 *
 *  
 */
angular.module('JobModalEventDefinition', [])
    .value(
    'JobModalEventForm', {
        
        editTitle: '{{ id }} - {{ event_display }}',                         //Legend in edit mode
        name: 'job_events',
        well: false,
        'class': 'horizontal-narrow',

        fields: {
            event_data: {
                label: 'Event Data',
                type: 'textarea',
                readonly: true,
                rows: 10,
                'class': 'modal-input-xlarge'
                } 
            },

        buttons: {
            },

        related: { //related colletions (and maybe items?)   
            }
            
    }); //Form

