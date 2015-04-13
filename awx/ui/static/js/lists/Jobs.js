/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Jobs.js
 *  List view object for job data model.
 *
 *  Used on dashboard to provide a list of all jobs, regardless of
 *  status.
 *
 */



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
                ngClick:"viewJobLog(job.id)",
                key: true,
                desc: true,
                searchType: 'int',
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2',
                awToolTip: "{{ job.status_tip }}",
                awTipPlacement: "top",
            },
            status: {
                label: 'Status',
                columnClass: 'col-lg-1 col-md-2 col-sm-2 col-xs-2',
                awToolTip: "{{ job.status_tip }}",
                awTipPlacement: "top",
                dataTitle: "{{ job.status_popover_title }}",
                icon: 'icon-job-{{ job.status }}',
                iconOnly: true,
                ngClick:"viewJobLog(job.id)",
                searchable: true,
                nosort: true,
                searchType: 'select',
                searchOptions: [
                    { name: "Success", value: "successful" },
                    { name: "Error", value: "error" },
                    { name: "Failed", value: "failed" },
                    { name: "Canceled", value: "canceled" }
                ]
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
                ngBind: 'job.type_label',
                link: false,
                columnClass: "col-lg-2 col-md-2 hidden-sm hidden-xs",
                searchable: true,
                searchType: 'select',
                searchOptions: []    // populated via GetChoices() in controller
            },
            name: {
                label: 'Name',
                columnClass: 'col-md-3 col-xs-5',
                ngClick: "viewJobLog(job.id, job.nameHref)",
                defaultSearchField: true
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
            },
            stdout: {
                mode: 'all',
                href: '/#/jobs/{{ job.id }}/stdout',
                awToolTip: 'View standard output',
                dataPlacement: 'top',
                ngShow: "job.type == 'job'"
            }
        }
    });
