/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  JobEvents.js
 *  Form definition for Job Events model
 *
 *
 */
angular.module('JobEventFormDefinition', [])
    .value(
    'JobEventForm', {
        
        editTitle: '{{ id }} - {{ event }}',                         //Legend in edit mode
        name: 'job_events',
        well: true,
        
        fields: {
            id: {
                label: 'Event ID',
                type: 'text',
                readonly: true,
                class: 'span2'
                },
            event: {
                label: 'Event',
                type: 'text',
                readonly: true
                },
            created: {
                label: 'Created',
                type: 'text',
                readonly: true,
                class: 'span4'
                },
            host: {
                label: 'Host',
                type: 'text',
                readonly: true
                },
            status: {
                label: 'Status',
                type: 'text',
                class: 'job-\{\{ event_status \}\}',
                readonly: true
                },
            event_data: {
                label: 'Event Data',
                type: 'textarea',
                class: 'span12',
                rows: 10,
                readonly: true
                } 
            },

        buttons: { 

            },

        related: { //related colletions (and maybe items?)
           
            }
            
    }); //Form

