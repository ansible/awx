/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('AllJobsDefinition', ['sanitizeFilter', 'capitalizeFilter'])
    .value( 'AllJobsList', {

        name: 'jobs',
        basePath: 'unified_jobs',
        iterator: 'job',
        editTitle: 'All Jobs',
        index: false,
        hover: true,
        well: false,
        fields: {
            status: {
                label: '',
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2 List-staticColumn--smallStatus',
                dataTipWatch: 'job.status_tip',
                awToolTip: "{{ job.status_tip }}",
                awTipPlacement: "right",
                dataTitle: "{{ job.status_popover_title }}",
                icon: 'icon-job-{{ job.status }}',
                iconOnly: true,
                ngClick:"viewJobDetails(job)",
                nosort: true
            },
            id: {
                label: 'ID',
                ngClick:"viewJobDetails(job)",
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2 List-staticColumnAdjacent',
                awToolTip: "{{ job.status_tip }}",
                dataPlacement: 'top',
                noLink: true
            },
            name: {
                label: 'Name',
                columnClass: 'col-lg-2 col-md-3 col-sm-4 col-xs-6',
                ngClick: "viewJobDetails(job)",
            },
            type: {
                label: 'Type',
                ngBind: 'job.type_label',
                link: false,
                columnClass: "col-lg-2 hidden-md hidden-sm hidden-xs",
                columnShow: "showJobType",
            },
            finished: {
                label: 'Finished',
                noLink: true,
                filter: "longDate",
                columnClass: "col-lg-2 col-md-3 col-sm-3 hidden-xs",
                key: true,
                desc: true
            },
            labels: {
                label: 'Labels',
                type: 'labels',
                nosort: true,
                showDelete: false,
                columnClass: 'List-tableCell col-lg-4 col-md-4 hidden-sm hidden-xs',
                sourceModel: 'labels',
                sourceField: 'name'
            },
        },

        actions: { },

        fieldActions: {

            columnClass: 'col-lg-2 col-md-2 col-sm-3 col-xs-4',
            "view": {
                mode: "all",
                ngClick: "viewJob(job.id)",
                awToolTip: "View the job",
                dataPlacement: "top"
            },
            submit: {
                icon: 'icon-rocket',
                mode: 'all',
                ngClick: 'relaunchJob($event, job.id)',
                awToolTip: 'Relaunch using the same parameters',
                dataPlacement: 'top',
                ngShow: "!(job.type == 'system_job') && job.summary_fields.user_capabilities.start"
            },
            cancel: {
                mode: 'all',
                ngClick: 'deleteJob(job.id)',
                awToolTip: 'Cancel the job',
                dataPlacement: 'top',
                ngShow: "(job.status === 'running'|| job.status === 'waiting' || job.status === 'pending') && job.summary_fields.user_capabilities.start"
            },
            "delete": {
                mode: 'all',
                ngClick: 'deleteJob(job.id)',
                awToolTip: 'Delete the job',
                dataPlacement: 'top',
                ngShow: "(job.status !== 'running' && job.status !== 'waiting' && job.status !== 'pending') && job.summary_fields.user_capabilities.delete"
            }
        }
    });
