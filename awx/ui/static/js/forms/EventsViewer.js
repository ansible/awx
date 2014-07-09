/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobEventsForm.js
 *
 */
angular.module('EventsViewerFormDefinition', [])
    .value('EventsViewerForm', {

        fields: {
            status: {
                label: 'Status',
                section: 'Event'
            },
            id: {
                label: 'ID',
                section: 'Event'
            },
            created: {
                label: 'Created On',
                section: 'Event'
            },
            host_name: {
                label: 'Host',
                section: 'Event'
            },
            play: {
                label: 'Play',
                type: 'text',
                section: 'Event'
            },
            task: {
                label: 'Task',
                section: 'Event'
            },
            role: {
                label: 'Role',
                section: 'Event'
            },
            rc: {
                label: 'Return Code',
                section: 'Results'
            },
            msg: {
                label: 'Message',
                section: 'Results'
            },
            results: {
                label: 'Results',
                section: 'Results'
            },
            start: {
                label: 'Start',
                section: 'Timing'
            },
            end: {
                label: 'End',
                section: 'Timing'
            },
            delta: {
                label: 'Elapsed',
                section: 'Timing'
            },
            module_name: {
                label: 'Name',
                section: 'Module'
            },
            module_args: {
                label: 'Arguments',
                section: 'Module'
            }
        }
    });