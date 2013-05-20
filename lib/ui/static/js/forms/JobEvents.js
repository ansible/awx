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
        
        editTitle: '{{ name }} Events',                         //Legend in edit mode
        name: 'job_events',
        well: true,
        formInline: true,
        
        fields: {
            job: {
                label: 'Job ID',
                type: 'text',
                readonly: true
                },
            name: {
                label: 'Name',
                type: 'text',
                sourceModel: 'job',
                sourceField: 'name',
                readonly: true
                },
            description: { 
                label: 'Description',
                type: 'text',
                sourceModel: 'job',
                sourceField: 'description',
                readonly: true
                }
            },

        buttons: { 

            },

        items: {
            event: {
                label: 'Event',
                type: 'text',
                readonly: true
                },
            created: {
                label: 'Event Timestamp',
                type: 'text',
                readonly: true
                },
            event_status: {
                label: 'Event Status <span class="job-detail-status job-\{\{ status \}\}"><i class="icon-circle"></i> \{\{ status \}\}</span>',
                type: 'text',
                readonly: true,
                control: false
                },
            event_data: {
                label: 'Event Data',
                type: 'textarea',
                class: 'span12',
                rows: 10
                } 
            },

        related: { //related colletions (and maybe items?)
           
            }
            
    }); //Form

