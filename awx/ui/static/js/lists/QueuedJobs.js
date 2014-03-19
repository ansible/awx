/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  QueuedJobs.js
 *
 * 
 */

'use strict';

angular.module('QueuedJobsDefinition', [])
    .value( 'QueuedJobsList', {
        
        name: 'queued_jobs',
        iterator: 'queued_job',
        editTitle: 'Queued Jobs',
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
                columnClass: 'hidden-sm hidden-xs'
            },
            job_template: {
                label: 'Job Template',
                ngBind: 'queued_job.summary_fields.job_template.name',
                //ngHref: "{{ '/#/job_templates/?name=' + queued_job.summary_fields.job_template.name }}",
                ngHref:"{{ '/#/job_templates/' + queued_job.job_template }}",
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
                "class": 'job-{{ queued_job.status }}',
                searchType: 'select',
                linkTo: "{{ queued_job.statusLinkTo }}",
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
                badgeIcon: 'fa icon-job-{{ queued_job.status }}',
                badgePlacement: 'left',
                badgeToolTip: "{{ queued_job.statusBadgeToolTip }}",
                badgeTipPlacement: 'top',
                badgeNgHref: "{{ queued_job.statusLinkTo }}",
                awToolTip: "{{ queued_job.statusBadgeToolTip }}",
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
                ngClick: 'submitJob(queued_job.id, queued_job.summary_fields.job_template.name)',
                awToolTip: 'Start the job',
                dataPlacement: 'top'
            },
            cancel: {
                label: 'Stop',
                mode: 'all',
                ngClick: 'deleteJob(queued_job.id)',
                awToolTip: 'Cancel a running or pending job',
                ngShow: "queued_job.status == 'pending' || queued_job.status == 'running' || queued_job.status == 'waiting'",
                dataPlacement: 'top'
            },
            "delete": {
                label: 'Delete',
                mode: 'all',
                ngClick: 'deleteJob(queued_job.id)',
                awToolTip: 'Delete the job',
                ngShow: "queued_job.status != 'pending' && queued_job.status != 'running' && queued_job.status != 'waiting'",
                dataPlacement: 'top'
            },
            dropdown: {
                type: 'DropDown',
                label: 'View',
                icon: 'fa-search-plus',
                'class': 'btn-default btn-xs',
                options: [
                    { ngClick: 'editJob(queued_job.id, queued_job.summary_fields.job_template.name)', label: 'Status' },
                    { ngClick: 'viewEvents(queued_job.id, queued_job.summary_fields.job_template.name)', label: 'Events',
                        ngHide: "queued_job.status == 'new'" },
                    { ngClick: 'viewSummary(queued_job.id, queued_job.summary_fields.job_template.name)', label: 'Host Summary',
                        ngHide: "queued_job.status == 'new'" }
                ]
            }
        }
    });
