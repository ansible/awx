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
        
        editTitle: '{{ id }} - {{ event_display }}',                         //Legend in edit mode
        name: 'job_events',
        well: false,
        
        fields: {
            status: {
                labelClass: 'job-\{\{ status \}\}',
                icon: 'icon-circle',
                type: 'custom',
                control: '<div class=\"job-event-status job-\{\{ status \}\}\">\{\{ status \}\}</div>',
                section: 'Event'
                },
            id: {
                label: 'ID',
                type: 'text',
                readonly: true,
                section: 'Event',
                'class': 'span1'
                },
            created: {
                label: 'Created',
                type: 'text',
                readonly: true,
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
                readonly: true,
                section: 'Event'
                },
            rc: {
                label: 'Return Code',
                type: 'text',
                readonly: true,
                section: 'Results',
                'class': 'span1'
                }, 
            msg: {
                label: 'Message',
                type: 'textarea',
                readonly: true,
                section: 'Results',
                'class': 'span12',
                rows: 1
                },
            stdout: {
                label: 'Std Out',
                type: 'textarea',
                readonly: true,
                section: 'Results',
                'class': 'span12',
                rows: 1
                },
            stderr: {
                label: 'Std Error',
                type: 'textarea',
                readonly: true,
                section: 'Results',
                'class': 'span12',
                rows: 1
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

        navigation: {
            back_top: {
                label: 'Back', 
                position: 'top',
                'class': 'btn-small pull-right',
                icon:  'icon-arrow-left',
                ngClick: 'navigateBack()'
                },
            back_bottom: {
                label: 'Back', 
                position: 'bottom',
                'class': 'btn-small pull-right',
                icon:  'icon-arrow-left',
                ngClick: 'navigateBack()'
                },
            raw_view: {
                label: 'View raw JSON results', 
                icon: 'icon-zoom-in',
                position: 'bottom',
                'class': 'btn-small',
                ngClick: 'rawView()'
                }
            },

        buttons: {
            },

        related: { //related colletions (and maybe items?)
           
            }
            
    }); //Form

