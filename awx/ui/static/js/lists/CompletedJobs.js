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
        index: false,
        hover: true,
        well: false,
        
        fields: {
            id: {
                label: 'Job ID',
                key: true,
                desc: true,
                searchType: 'int',
                columnClass: 'col-lg-1 col-md-2 col-sm-2 col-xs-2'
            },
            inventory: {
                label: 'Inventory ID',
                searchType: 'int',
                searchOnly: true
            },
            created: {
                label: 'Create On',
                link: false,
                searchable: false,
                filter: "date:'MM/dd/yy HH:mm:ss'",
                columnClass: "hidden-sm hidden-xs"
            },
            job_template: {
                label: 'Job Template',
                ngBind: 'completed_job.summary_fields.job_template.name',
                //ngHref: "{{ '/#/job_templates/?name=' + completed_job.summary_fields.job_template.name }}",
                ngHref:"{{ '/#/job_templates/' + completed_job.job_template }}",
                sourceModel: 'job_template',
                sourceField: 'name',
                columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-3'
            },
            failed: {
                label: 'Job failed?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true,
                nosort: true
            },
            status: {
                label: 'Status',
                "class": 'job-{{ completed_job.status }}',
                searchType: 'select',
                linkTo: "{{ completed_job.statusLinkTo }}",
                searchOptions: [
                    { name: "new", value: "new" },
                    { name: "waiting", value: "waiting" },
                    { name: "pending", value: "pending" },
                    { name: "running", value: "running" },
                    { name: "successful", value: "successful" },
                    { name: "error", value: "error" },
                    { name: "failed", value: "failed" },
                    { name: "canceled", value: "canceled" }
                ],
                badgeIcon: 'fa icon-job-{{ completed_job.status }}',
                badgePlacement: 'left',
                badgeToolTip: "{{ completed_job.statusBadgeToolTip }}",
                badgeTipPlacement: 'top',
                badgeNgHref: "{{ completed_job.statusLinkTo }}",
                awToolTip: "{{ completed_job.statusBadgeToolTip }}",
                dataPlacement: 'top'
            }
        },
        
        actions: {
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refresh()"
            }
        },

        fieldActions: {
            submit: {
                label: 'Relaunch',
                icon: 'icon-rocket',
                mode: 'all',
                ngClick: 'submitJob(completed_job.id, completed_job.summary_fields.job_template.name)',
                awToolTip: 'Start the job',
                dataPlacement: 'top'
            },
            cancel: {
                label: 'Stop',
                mode: 'all',
                ngClick: 'deleteJob(completed_job.id)',
                awToolTip: 'Cancel a running or pending job',
                ngShow: "completed_job.status == 'pending' || completed_job.status == 'running' || completed_job.status == 'waiting'",
                dataPlacement: 'top'
            },
            "delete": {
                label: 'Delete',
                mode: 'all',
                ngClick: 'deleteJob(completed_job.id)',
                awToolTip: 'Delete the job',
                ngShow: "completed_job.status != 'pending' && completed_job.status != 'running' && completed_job.status != 'waiting'",
                dataPlacement: 'top'
            },
            dropdown: {
                type: 'DropDown',
                label: 'View',
                icon: 'fa-search-plus',
                'class': 'btn-default btn-xs',
                options: [
                    { ngClick: 'editJob(completed_job.id, completed_job.summary_fields.job_template.name)', label: 'Status' },
                    { ngClick: 'viewEvents(completed_job.id, completed_job.summary_fields.job_template.name)', label: 'Events',
                        ngHide: "completed_job.status == 'new'" },
                    { ngClick: 'viewSummary(completed_job.id, completed_job.summary_fields.job_template.name)', label: 'Host Summary',
                        ngHide: "completed_job.status == 'new'" }
                ]
            }
        }
    });
