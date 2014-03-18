/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  RunningJobs.js 
 *
 * 
 */

'use strict';

angular.module('RunningJobsDefinition', [])
    .value( 'RunningJobsList', {
        
        name: 'running_jobs',
        iterator: 'running_job',
        editTitle: 'Completed Jobs',
        index: false,
        hover: true,
        well: false,
        
        fields: {
            id: {
                label: 'Job ID',
                key: true,
                desc: true,
                searchType: 'int'
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
                filter: "date:'MM/dd HH:mm:ss'"
            },
            job_template: {
                label: 'Job Template',
                ngBind: 'running_job.summary_fields.job_template.name',
                //ngHref: "{{ '/#/job_templates/?name=' + running_job.summary_fields.job_template.name }}",
                ngHref:"{{ '/#/job_templates/' + running_job.job_template }}",
                sourceModel: 'job_template',
                sourceField: 'name'
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
                "class": 'job-{{ running_job.status }}',
                searchType: 'select',
                linkTo: "{{ running_job.statusLinkTo }}",
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
                badgeIcon: 'fa icon-job-{{ running_job.status }}',
                badgePlacement: 'left',
                badgeToolTip: "{{ running_job.statusBadgeToolTip }}",
                badgeTipPlacement: 'top',
                badgeNgHref: "{{ running_job.statusLinkTo }}",
                awToolTip: "{{ running_job.statusBadgeToolTip }}",
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
                ngClick: 'submitJob(running_job.id, running_job.summary_fields.job_template.name)',
                awToolTip: 'Start the job',
                dataPlacement: 'top'
            },
            cancel: {
                label: 'Stop',
                mode: 'all',
                ngClick: 'deleteJob(running_job.id)',
                awToolTip: 'Cancel a running or pending job',
                ngShow: "running_job.status == 'pending' || running_job.status == 'running' || running_job.status == 'waiting'",
                dataPlacement: 'top'
            },
            "delete": {
                label: 'Delete',
                mode: 'all',
                ngClick: 'deleteJob(running_job.id)',
                awToolTip: 'Delete the job',
                ngShow: "running_job.status != 'pending' && running_job.status != 'running' && running_job.status != 'waiting'",
                dataPlacement: 'top'
            },
            dropdown: {
                type: 'DropDown',
                label: 'View',
                icon: 'fa-search-plus',
                'class': 'btn-default btn-xs',
                options: [
                    { ngClick: 'editJob(running_job.id, running_job.summary_fields.job_template.name)', label: 'Status' },
                    { ngClick: 'viewEvents(running_job.id, running_job.summary_fields.job_template.name)', label: 'Events',
                        ngHide: "running_job.status == 'new'" },
                    { ngClick: 'viewSummary(running_job.id, running_job.summary_fields.job_template.name)', label: 'Host Summary',
                        ngHide: "running_job.status == 'new'" }
                ]
            }
        }
    });
