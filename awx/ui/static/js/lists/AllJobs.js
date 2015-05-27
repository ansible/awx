/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 

export default
    angular.module('AllJobsDefinition', ['sanitizeFilter', 'capitalizeFilter'])
    .value( 'AllJobsList', {

        name: 'all_jobs',
        iterator: 'all_job',
        editTitle: 'All Jobs',
        index: false,
        hover: true,
        well: false,

        fields: {
            id: {
                label: 'ID',
                ngClick:"viewJobLog(all_job.id)",
                searchType: 'int',
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2',
                awToolTip: "{{ all_job.status_tip }}",
                dataPlacement: 'top'
            },
            status: {
                label: 'Status',
                columnClass: 'col-lg-2 col-md-2 col-sm-2 col-xs-2',
                awToolTip: "{{ all_job.status_tip }}",
                awTipPlacement: "top",
                dataTitle: "{{ all_job.status_popover_title }}",
                icon: 'icon-job-{{ all_job.status }}',
                alt_text: "{{all_job.status_label}}",
                iconOnly: true,
                ngClick:"viewJobLog(all_job.id)",
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
                filter: "longDate",
                columnClass: "col-lg-2 col-md-2 hidden-xs",
                key: true,
                desc: true
            },
            type: {
                label: 'Type',
                ngBind: 'all_job.type_label',
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
                ngClick: "viewJobLog(all_job.id, all_job.nameHref)",
                defaultSearchField: true,
                awToolTip: "{{ all_job.name | sanitize }}",
                dataPlacement: 'top'
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
                ngClick: 'relaunchJob($event, all_job.id)',
                awToolTip: 'Relaunch using the same parameters',
                dataPlacement: 'top',
                ngHide: "all_job.type == 'system_job' "
            },
            cancel: {
                mode: 'all',
                ngClick: 'deleteJob(all_job.id)',
                awToolTip: 'Cancel the job',
                dataPlacement: 'top',
                ngShow: "all_job.status === 'running'|| all_job.status == 'waiting' || all_job.status == 'pending'"
            },
            "delete": {
                mode: 'all',
                ngClick: 'deleteJob(all_job.id)',
                awToolTip: 'Delete the job',
                dataPlacement: 'top',
                ngShow: "all_job.status !== 'running' && all_job.status !== 'waiting' && all_job.status !== 'pending'"
            },
            stdout: {
                mode: 'all',
                href: '/#/jobs/{{ all_job.id }}/stdout',
                awToolTip: 'View standard output',
                dataPlacement: 'top',
                ngShow: "all_job.type == 'job'"
            }
        }
    });
