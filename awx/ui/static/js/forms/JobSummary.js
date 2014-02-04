/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobSummary.js
 *
 *  Display job status info in a dialog
 *
 */
angular.module('JobSummaryDefinition', [])
    .value(
    'JobSummary', {
        
        editTitle: '{{ id }} - {{ name }}',
        name: 'jobs',
        well: false,
        
        fields: {
            status: {
                //label: 'Job Status',
                type: 'custom',
                control: '<div class=\"job-detail-status\"><span style="padding-right: 15px; font-weight: bold;">Status</span> ' +
                    '<i class=\"fa icon-job-{{ status }}\"></i> {{ status }}</div>',
                readonly: true
                },
            created: {
                label: 'Created On',
                type: 'text',
                readonly: true
                },
            result_stdout: {
                label: 'Standard Out',
                type: 'textarea',
                readonly: true,
                xtraWide: true,
                rows: '{{ stdout_rows }}',
                'class': 'nowrap mono-space resizable',
                ngShow: 'result_stdout != ""'
                },
            result_traceback: {
                label: 'Traceback',
                type: 'textarea',
                xtraWide: true,
                readonly: true,
                rows: '{{ traceback_rows }}',
                'class': 'nowrap mono-space resizable',
                ngShow: 'result_traceback != ""'
                }
        }
        
    });