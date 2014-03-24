/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  QueuedJobs.js
 *
 * 
 */

'use strict';

angular.module('QueuedJobsDefinition', [])
    .value( 'QueuedJobsList', {
        
        name: 'queued_jobs',
        iterator: 'queued_job',
        editTitle: 'Queued Jobs',
        'class': 'table-condensed',
        index: false,
        hover: true,
        well: false,
        
        fields: {
            id: {
                label: 'Job ID',
                key: true,
                desc: true,
                searchType: 'int',
                columnClass: 'col-md-1 col-sm-2 col-xs-2'
            },
            inventory: {
                label: 'Inventory ID',
                searchType: 'int',
                searchOnly: true
            },
            created: {
                label: 'Created On',
                link: false,
                searchable: false,
                filter: "date:'MM/dd/yy HH:mm:ss'",
                columnClass: 'col-md-2 hidden-xs'
            },
            next_job_run: {
                label: 'Next Run',
                searchable: false,
                filter: "date:'MM/dd/yy HH:mm:ss'",
                columnClass: "col-md-2 hidden-sm hidden-xs"
            },
            type: {
                label: 'Type',
                link: false,
                columnClass: "col-md-2 hidden-sm hidden-xs"
            },
            name: {
                label: 'Name',
                columnClass: 'col-sm-3 col-xs-5',
                ngHref: 'nameHref',
                sourceModel: 'template',
                sourceField: 'name'
            }
        },

        actions: {
            columnClass: 'col-md-2 col-sm-3 col-xs-3',
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refresh()"
            }
        },

        fieldActions: {
            status: {
                mode: 'all',
                iconClass: 'fa icon-job-{{ queued_job.status }}',
                awToolTip: "{{ queued_job.statusToolTip }}",
                dataPlacement: 'top'
            },
            submit: {
                icon: 'icon-rocket',
                mode: 'all',
                ngClick: 'submitJob(queued_job.id, queued_job.summary_fields.job_template.name)',
                awToolTip: 'Launch another instance of the job',
                dataPlacement: 'top'
            },
            cancel: {
                mode: 'all',
                ngClick: 'deleteJob(queued_job.id)',
                awToolTip: 'Cancel the job',
                dataPlacement: 'top'
            }
        }
    });
