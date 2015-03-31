/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  QueuedJobs.js
 *
 *
 */



export default
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
                label: 'ID',
                ngClick:"viewJobLog(queued_job.id)",
                key: true,
                searchType: 'int',
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2',
                awToolTip: "{{ queued_job.status_tip }}",
                awTipPlacement: "top",
            },
            status: {
                label: 'Status',
                columnClass: 'col-lg-1 col-md-2 col-sm-2 col-xs-2',
                awToolTip: "{{ queued_job.status_tip }}",
                awTipPlacement: "top",
                dataTitle: "{{ queued_job.status_popover_title }}",
                icon: 'icon-job-{{ queued_job.status }}',
                iconOnly: true,
                ngClick:"viewJobLog(queued_job.id)",
                searchable: false,
                nosort: true
            },
            created: {
                label: 'Created',
                noLink: true,
                searchable: false,
                filter: "date:'MM/dd HH:mm:ss'",
                columnClass: 'col-lg-2 col-md-2 hidden-xs'
            },
            type: {
                label: 'Type',
                ngBind: 'queued_job.type_label',
                link: false,
                columnClass: "col-lg-2 col-md-2 hidden-sm hidden-xs",
                searchable: true,
                searchType: 'select',
                searchOptions: []    // populated via GetChoices() in controller
            },
            name: {
                label: 'Name',
                columnClass: 'col-md-3 col-sm-4 col-xs-4',
                ngClick: "viewJobLog(queued_job.id, queued_job.nameHref)",
                defaultSearchField: true
            }
        },

        actions: { },

        fieldActions: {
            submit: {
                icon: 'icon-rocket',
                mode: 'all',
                ngClick: 'relaunchJob($event, queued_job.id)',
                awToolTip: 'Relaunch using the same parameters',
                dataPlacement: 'top',
                ngHide: "queued_job.type == 'system_job' "
            },
            'cancel': {
                mode: 'all',
                ngClick: 'deleteJob(queued_job.id)',
                awToolTip: 'Cancel the job',
                dataPlacement: 'top'
            },
            job_details: {
                mode: 'all',
                ngClick: "viewJobLog(queued_job.id)",
                awToolTip: 'View job details',
                dataPlacement: 'top',
                ngShow: "queued_job.type == 'job'"
            }
        }
    });
