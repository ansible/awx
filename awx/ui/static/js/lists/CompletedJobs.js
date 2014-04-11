/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  CompletedJobs.js 
 *
 * 
 */

'use strict';

angular.module('CompletedJobsDefinition', [])
    .value( 'CompletedJobsList', {
        
        name: 'completed_jobs',
        iterator: 'completed_job',
        editTitle: 'Completed Jobs',
        'class': 'table-condensed',
        index: false,
        hover: true,
        well: false,
        
        fields: {
            id: {
                label: 'Job ID',
                ngClick:"viewJobLog(completed_job.id)",
                searchType: 'int',
                columnClass: 'col-md-1 col-sm-2 col-xs-2'
            },
            status: {
                label: 'Status',
                columnClass: 'col-md-2 col-sm-2 col-xs-2',
                awToolTip: "{{ completed_job.status_tip }}",
                awTipPlacement: "top",
                dataTitle: "{{ completed_job.status_popover_title }}",
                icon: 'icon-job-{{ completed_job.status }}',
                iconOnly: true,
                ngClick:"viewJobLog(completed_job.id)",
                searchType: 'select',
                searchOptions: [
                    { name: "Success", value: "successful" },
                    { name: "Error", value: "error" },
                    { name: "Failed", value: "failed" },
                    { name: "Canceled", value: "canceled" }
                ]
            },
            finished: {
                label: 'Finished On',
                noLink: true,
                searchable: false,
                filter: "date:'MM/dd/yy HH:mm:ss'",
                columnClass: "col-md-2 hidden-xs",
                key: true,
                desc: true
            },
            type: {
                label: 'Type',
                ngBind: 'completed_job.type_label',
                link: false,
                columnClass: "col-md-2 hidden-sm hidden-xs",
                columnShow: "showJobType",
                searchable: true,
                searchType: 'select',
                searchOptions: []    // populated via GetChoices() in controller
            },
            name: {
                label: 'Name',
                columnClass: 'col-md-3 col-xs-5',
                ngClick: "viewJobLog(completed_job.id, completed_job.nameHref)",
                defaultSearchField: true
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
                ngClick: 'relaunchJob($event, completed_job.id)',
                awToolTip: 'Relaunch using the same parameters',
                dataPlacement: 'top'
            },
            "delete": {
                mode: 'all',
                ngClick: 'deleteJob(completed_job.id)',
                awToolTip: 'Delete the job',
                dataPlacement: 'top'
            },
            dropdown: {
                type: 'DropDown',
                ngShow: "completed_job.type === 'job'",
                label: 'View',
                icon: 'fa-search-plus',
                'class': 'btn-default btn-xs',
                options: [
                    //{ ngHref: '/#/jobs/{{ completed_job.id }}', label: 'Status' },
                    { ngHref: '/#/job_events/{{ completed_job.id }}', label: 'Events', ngHide: "completed_job.status == 'new'" },
                    { ngHref: '/#/job_host_summaries/{{ completed_job.id }}', label: 'Host Summary' }
                ]
            }
        }
    });
