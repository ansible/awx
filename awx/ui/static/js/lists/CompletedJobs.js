/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  CompletedJobs.js
 *
 *
 */



angular.module('CompletedJobsDefinition', [])
    .value( 'CompletedJobsList', {

        name: 'completed_jobs',
        iterator: 'completed_job',
        editTitle: 'Completed Jobs',
        index: false,
        hover: true,
        well: false,

        fields: {
            id: {
                label: 'ID',
                ngClick:"viewJobLog(completed_job.id)",
                searchType: 'int',
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2',
                awToolTip: "{{ completed_job.status_tip }}",
                dataPlacement: 'top'
            },
            status: {
                label: 'Status',
                columnClass: 'col-lg-1 col-md-2 col-sm-2 col-xs-2',
                awToolTip: "{{ completed_job.status_tip }}",
                awTipPlacement: "top",
                dataTitle: "{{ completed_job.status_popover_title }}",
                icon: 'icon-job-{{ completed_job.status }}',
                iconOnly: true,
                ngClick:"viewJobLog(completed_job.id)",
                searchable: true,
                searchType: 'select',
                nosort: true,
                searchOptions: [
                    { name: "Success", value: "successful" },
                    { name: "Error", value: "error" },
                    { name: "Failed", value: "failed" },
                    { name: "Canceled", value: "canceled" }
                ]
            },
            finished: {
                label: 'Finished',
                noLink: true,
                searchable: false,
                filter: "date:'MM/dd HH:mm:ss'",
                columnClass: "col-lg-2 col-md-2 hidden-xs",
                key: true,
                desc: true
            },
            type: {
                label: 'Type',
                ngBind: 'completed_job.type_label',
                link: false,
                columnClass: "col-lg-2 col-md-2 hidden-sm hidden-xs",
                columnShow: "showJobType",
                searchable: true,
                searchType: 'select',
                searchOptions: []    // populated via GetChoices() in controller
            },
            name: {
                label: 'Name',
                columnClass: 'col-md-3 col-sm-4 col-xs-4',
                ngClick: "viewJobLog(completed_job.id, completed_job.nameHref)",
                defaultSearchField: true,
                awToolTipEllipses: "{{ completed_job.name }}"
            },
            failed: {
                label: 'Job failed?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true,
                nosort: true
            }
        },

        actions: { },

        fieldActions: {
            submit: {
                icon: 'icon-rocket',
                mode: 'all',
                ngClick: 'relaunchJob($event, completed_job.id)',
                awToolTip: 'Relaunch using the same parameters',
                dataPlacement: 'top',
                ngHide: "completed_job.type == 'system_job' "
            },
            "delete": {
                mode: 'all',
                ngClick: 'deleteJob(completed_job.id)',
                awToolTip: 'Delete the job',
                dataPlacement: 'top'
            },
            job_details: {
                mode: 'all',
                ngClick: "viewJobLog(completed_job.id)",
                awToolTip: 'View job details',
                dataPlacement: 'top'
            },
            stdout: {
                mode: 'all',
                href: '/#/jobs/{{ completed_job.id }}/stdout',
                awToolTip: 'View standard output',
                dataPlacement: 'top',
                ngShow: "completed_job.type == 'job'"
            }
        }
    });
