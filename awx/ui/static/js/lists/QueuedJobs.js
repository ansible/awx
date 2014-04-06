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
                ngClick:"viewJobLog(queued_job.id)",
                key: true,
                desc: true,
                searchType: 'int',
                columnClass: 'col-md-1 col-sm-2 col-xs-2'
            },
            status: {
                label: 'Status',
                columnClass: 'col-md-2 col-sm-2 col-xs-2',
                awToolTip: "{{ queued_job.status_tip }}",
                awTipPlacement: "top",
                dataTitle: "{{ queued_job.status_popover_title }}",
                icon: 'icon-job-{{ queued_job.status }}',
                iconOnly: true,
                ngClick:"viewJobLog(queued_job.id)",
                searchable: false
            },
            created: {
                label: 'Created On',
                noLink: true,
                searchable: false,
                filter: "date:'MM/dd/yy HH:mm:ss'",
                columnClass: 'col-md-2 hidden-xs'
            },
            type: {
                label: 'Type',
                ngBind: 'queued_job.type_label',
                link: false,
                columnClass: "col-md-2 hidden-sm hidden-xs",
                searchable: true,
                searchType: 'select',
                searchOptions: []    // populated via GetChoices() in controller
            },
            name: {
                label: 'Name',
                columnClass: 'col-sm-3 col-xs-5',
                ngClick: "viewJobLog(queued_job.id, queued_job.nameHref)",
                defaultSearchField: true
            }
        },

        actions: {
            columnClass: 'col-md-2 col-sm-3 col-xs-3',
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refreshJobs()"
            }
        },

        fieldActions: {
            submit: {
                icon: 'icon-rocket',
                mode: 'all',
                ngClick: 'relaunchJob($event, queued_job.id)',
                awToolTip: 'Relaunch using the same parameters',
                dataPlacement: 'top'
            },
            "delete": {
                mode: 'all',
                ngClick: 'deleteJob(queued_job.id)',
                awToolTip: 'Delete the job',
                dataPlacement: 'top'
            }
        }
    });
