/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobEventsForm.js
 *
 */
angular.module('JobEventsFormDefinition', [])
    .value('JobEventsForm', {
        
        name: 'job_events',
        well: false,
        forceListeners: true,
        
        fields: {
            status: {
                labelClass: 'job-{{ status }}',
                type: 'custom',
                section: 'Event',
                control: "<div class=\"job-event-status job-{{ status }}\"><i class=\"fa icon-job-{{ status }}\"></i> {{ status }}</div>"
            },
            id: {
                label: 'ID',
                type: 'text',
                readonly: true,
                section: 'Event',
                'class': 'span1'
            },
            created: {
                label: 'Created On',
                type: 'text',
                section: 'Event',
                readonly: true
            },
            host: {
                label: 'Host',
                type: 'text',
                readonly: true,
                section: 'Event',
                ngShow: "host !== ''"
            },
            play: {
                label: 'Play',
                type: 'text',
                readonly: true,
                section: 'Event',
                ngShow: "play !== ''"
            },
            task: {
                label: 'Task',
                type: 'text',
                readonly: true,
                section: 'Event',
                ngShow: "task !== ''"
            },
            rc: {
                label: 'Return Code',
                type: 'text',
                readonly: true,
                section: 'Results',
                'class': 'span1',
                ngShow: "rc !== ''"
            },
            msg: {
                label: 'Msg',
                type: 'textarea',
                readonly: true,
                section: 'Results',
                'class': 'nowrap',
                ngShow: "msg !== ''",
                rows: 10
            },
            stdout: {
                label: 'Standard Out',
                type: 'textarea',
                readonly: true,
                section: 'Results',
                'class': 'nowrap',
                ngShow: "stdout !== ''",
                rows: 10
            },
            stderr: {
                label: 'Standard Err',
                type: 'textarea',
                readonly: true,
                section: 'Results',
                'class': 'nowrap',
                ngShow: "stderr !== ''",
                rows: 10
            },
            results: {
                label: 'Results',
                type: 'textarea',
                section: 'Results',
                readonly: true,
                'class': 'nowrap',
                ngShow: "results !== ''",
                rows: 10
            },
            start: {
                label: 'Start',
                type: 'text',
                readonly: true,
                section: 'Timing',
                ngShow: "start !== ''"
            },
            traceback: {
                label: false,
                type: 'textarea',
                readonly: true,
                section: 'Traceback',
                'class': 'nowrap',
                ngShow: "traceback !== ''",
                rows: 10
            },
            end: {
                label: 'End',
                type: 'text',
                readonly: true,
                section: 'Timing',
                ngShow: "end !== ''"
            },
            delta: {
                label: 'Elapsed',
                type: 'text',
                readonly: true,
                section: 'Timing',
                ngShow: "delta !== ''"
            },
            module_name: {
                label: 'Name',
                type: 'text',
                readonly: true,
                section: 'Module',
                ngShow: "module_name !== ''"
            },
            module_args: {
                label: 'Args',
                type: 'text',
                readonly: true,
                section: 'Module',
                ngShow: "module_args !== ''"
            }
        }
    });