/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('JobsListDefinition', [])
    .value( 'JobsList', {

        name: 'jobs',
        iterator: 'job',
        editTitle: 'Jobs',
        'class': 'table-condensed',
        index: false,
        hover: true,
        well: false,

        fields: {
            id: {
                label: 'ID',
                ngClick:"viewJobDetails(job)",
                key: true,
                desc: true,
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2',
                awToolTip: "{{ job.status_tip }}",
                awTipPlacement: "top",
            },
            status: {
                label: '',
                columnClass: 'col-lg-1 col-md-2 col-sm-2 col-xs-2',
                awToolTip: "{{ job.status_tip }}",
                awTipPlacement: "top",
                dataTitle: "{{ job.status_popover_title }}",
                icon: 'icon-job-{{ job.status }}',
                iconOnly: true,
                ngClick:"viewJobDetails(job)"
            },
            started: {
                label: 'Started',
                noLink: true,
                filter: "longDate",
                columnClass: "col-lg-2 col-md-2 hidden-xs"
            },
            type: {
                label: 'Type',
                ngBind: 'job.type_label',
                link: false,
                columnClass: "col-lg-2 col-md-2 hidden-sm hidden-xs"
            },
            name: {
                label: 'Name',
                columnClass: 'col-md-3 col-xs-5',
                ngClick: "viewJobDetails(job)",
            }
        },

        actions: { },

        fieldActions: {
            submit: {
                mode: 'all',
                icon: 'icon-rocket',
                ngClick: 'relaunchJob($event, job.id)',
                awToolTip: 'Relaunch using the same parameters',
                dataPlacement: 'top',
                ngHide: "job.type == 'system_job' "
            },
            cancel: {
                mode: 'all',
                ngClick: 'deleteJob(job.id)',
                awToolTip: 'Cancel the job',
                dataPlacement: 'top',
                ngShow: "job.status == 'running'"
            },
            "delete": {
                mode: 'all',
                ngClick: 'deleteJob(job.id)',
                awToolTip: 'Delete the job',
                dataPlacement: 'top',
                ngShow: "job.status != 'running'"
            }
        }
    });
