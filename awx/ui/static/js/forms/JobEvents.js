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
        "class": 'horizontal-narrow',
        well: false,
        
        fields: {
            created: {
                label: 'Created',
                type: 'text',
                readonly: true,
                "class": 'span3',
                section: 'Event Info'
                },
            status: {
                labelClass: 'job-\{\{ status \}\}',
                icon: 'icon-circle',
                type: 'custom',
                control: '<div class=\"job-event-status job-\{\{ status \}\}\">\{\{ status \}\}</div>',
                section: 'Event'
                },
            host: {
                label: 'Host',
                type: 'text',
                readonly: true,
                section: 'Event'
                },
            task: {
                label: 'Task',
                type: 'text',
                readonly: true,
                section: 'Event'
                },
            conditional: {
                label: 'Conditional?',
                type: 'checkbox',
                readonly: true
                },
            msg: {
                label: 'Message',
                type: 'textarea',
                readonly: true,
                section: 'Results',
                rows: 5
                },
            stdout: {
                label: 'Standard Out',
                type: 'textarea',
                readonly: true,
                section: 'Results',
                rows: 5
                },
            stderr: {
                label: 'Standard Error',
                type: 'textarea',
                readonly: true,
                section: 'Results',
                rows: 5
                },
            start: {
                label: 'Start',
                type: 'text',
                readonly: true, 
                section: 'Timing'
                },
            end: {
                label: 'End',
                type: 'text',
                readonly: true, 
                section: 'Timing'
                },
            delta: {
                label: 'Elapsed',
                type: 'text',
                readonly: true, 
                section: 'Timing'
                },
            module_name: {
                label: 'Name',
                type: 'text',
                readonly: true,
                section: 'Module'
                },
            module_args: {
                label: 'Arguments',
                type: 'text',
                readonly: true,
                section: 'Module'
                } 
            },

        buttons: { 

            },

        related: { //related colletions (and maybe items?)
           
            }
            
    }); //Form

