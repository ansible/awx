/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/




export default
    angular.module('CompletedJobsDefinition', ['sanitizeFilter'])
    .value( 'CompletedJobsList', {
        // These tooltip fields are consumed to build disabled related tabs tooltips in the form > add view
        awToolTip: 'Please save and run a job to view',
        dataPlacement: 'top',
        name: 'completed_jobs',
        basePath: 'job_templates/:id/jobs/?or__status=successful&or__status=failed&or__status=error&or__status=canceled',
        iterator: 'completed_job',
        editTitle: 'Completed Jobs',
        index: false,
        hover: true,
        well: false,
        emptyListText: 'No completed jobs',

        fields: {
            status: {
                label: '',
                searchLabel: 'Status',
                columnClass: 'List-staticColumn--smallStatus',
                awToolTip: "{{ completed_job.status_tip }}",
                awTipPlacement: "right",
                dataTitle: "{{ completed_job.status_popover_title }}",
                icon: 'icon-job-{{ completed_job.status }}',
                iconOnly: true,
                ngClick:"viewJobDetails(completed_job)",
                searchable: true,
                searchType: 'select',
                nosort: true,
                searchOptions: [
                    { label: "Success", value: "successful" },
                    { label: "Error", value: "error" },
                    { label: "Failed", value: "failed" },
                    { label: "Canceled", value: "canceled" }
                ]
            },
            id: {
                label: 'ID',
                ngClick:"viewJobDetails(completed_job)",
                searchType: 'int',
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2 List-staticColumnAdjacent',
                awToolTip: "{{ completed_job.status_tip }}",
                dataPlacement: 'top'
            },
            name: {
                label: 'Name',
                columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-6',
                ngClick: "viewJobDetails(completed_job)",
                defaultSearchField: true,
                awToolTip: "{{ completed_job.name | sanitize }}",
                dataPlacement: 'top'
            },
            finished: {
                label: 'Finished',
                noLink: true,
                searchable: false,
                filter: "longDate",
                columnClass: "col-lg-3 col-md-3 col-sm-3 hidden-xs",
                key: true,
                desc: true
            },
            type: {
                label: 'Type',
                ngBind: 'completed_job.type_label',
                link: false,
                columnClass: "col-lg-2 col-md-2 hidden-sm hidden-xs",
                columnShow: "showJobType",
                searchOnly: true,
                searchType: 'select',
                searchOptions: []    // populated via GetChoices() in controller
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

            columnClass: 'col-lg-2 col-md-2 col-sm-3 col-xs-4',

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
            }
        }
    });
