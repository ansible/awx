/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  RunningJobs.js
 *
 *
 */



export default
    angular.module('RunningJobsDefinition', ['sanitizeFilter'])
    .value( 'RunningJobsList', {

        name: 'running_jobs',
        iterator: 'running_job',
        editTitle: 'Completed Jobs',
        'class': 'table-condensed',
        index: false,
        hover: true,
        well: false,

        fields: {
            id: {
                label: 'ID',
                ngClick:"viewJobLog(running_job.id)",
                key: true,
                desc: true,
                searchType: 'int',
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2',
                awToolTip: "{{ running_job.status_tip }}",
                awTipPlacement: "top",
            },
            status: {
                label: 'Status',
                columnClass: 'col-lg-1 col-md-2 col-sm-2 col-xs-2',
                awToolTip: "{{ running_job.status_tip }}",
                awTipPlacement: "top",
                dataTitle: "{{ running_job.status_popover_title }}",
                icon: 'icon-job-{{ running_job.status }}',
                iconOnly: true,
                ngClick:"viewJobLog(running_job.id)",
                searchable: false,
                nosort: true
            },
            started: {
                label: 'Started',
                noLink: true,
                searchable: false,
                filter: "date:'MM/dd HH:mm:ss'",
                columnClass: "col-lg-2 col-md-2 hidden-xs"
            },
            type: {
                label: 'Type',
                ngBind: 'running_job.type_label',
                link: false,
                columnClass: "col-lg-2 col-md-2 hidden-sm hidden-xs",
                searchable: true,
                searchType: 'select',
                searchOptions: []    // populated via GetChoices() in controller
            },
            name: {
                label: 'Name',
                columnClass: 'col-md-3 col-sm-4 col-xs-4',
                ngClick: "viewJobLog(running_job.id, running_job.nameHref)",
                defaultSearchField: true,
                awToolTip: "{{ running_job.name | sanitize }}",
                awTipPlacement: "top"
            }
        },

        actions: { },

        fieldActions: {
            submit: {
                icon: 'icon-rocket',
                mode: 'all',
                ngClick: 'relaunchJob($event, running_job.id)',
                awToolTip: 'Relaunch using the same parameters',
                dataPlacement: 'top',
                ngHide: "running_job.type == 'system_job' "
            },
            cancel: {
                mode: 'all',
                ngClick: 'deleteJob(running_job.id)',
                awToolTip: 'Cancel the job',
                dataPlacement: 'top'
            },
            job_details: {
                mode: 'all',
                ngClick: "viewJobLog(running_job.id)",
                awToolTip: 'View job details',
                dataPlacement: 'top'
            },
            stdout: {
                mode: 'all',
                href: '/#/jobs/{{ running_job.id }}/stdout',
                awToolTip: 'View standard output',
                dataPlacement: 'top',
                ngShow: "running_job.type == 'job'"
            }
        }
    });
