/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Jobs.js 
 *  List view object for Team data model.
 *
 * 
 */
angular.module('JobsListDefinition', [])
    .value(
    'JobList', {
        
        name: 'jobs',
        iterator: 'job',
        editTitle: 'Jobs',
        index: false,
        hover: true,
        "class": 'jobs-table',
        
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
                label: 'Date',
                link: false,
                searchable: false
                },
            job_template: {
                label: 'Job Template',
                ngBind: 'job.summary_fields.job_template.name',
                //ngHref: "\{\{ '/#/job_templates/?name=' + job.summary_fields.job_template.name \}\}",
                ngHref:"\{\{ '/#/job_templates/' + job.job_template \}\}",
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
                "class": 'job-\{\{ job.status \}\}',
                searchType: 'select',
                linkTo: "\{\{ job.statusLinkTo \}\}",
                searchOptions: [
                    { name: "new", value: "new" },
                    { name: "waiting", value: "waiting" },
                    { name: "pending", value: "pending" },
                    { name: "running", value: "running" }, 
                    { name: "successful", value: "successful" },
                    { name: "error", value: "error" },
                    { name: "failed", value: "failed" },
                    { name: "canceled", value: "canceled" } ],
                badgeIcon: 'icon-job-\{\{ job.status \}\}',
                badgePlacement: 'left',
                badgeToolTip: "\{\{ job.statusBadgeToolTip \}\}",
                badgeTipPlacement: 'top',
                badgeNgHref: "\{\{ job.statusLinkTo \}\}",
                awToolTip: "\{\{ job.statusBadgeToolTip \}\}",
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
            rerun: {
                label: 'Launch',
                icon: 'icon-rocket',
                mode: 'all',             
                ngClick: "submitJob(\{\{ job.id \}\}, '\{\{ job.summary_fields.job_template.name \}\}' )",
                "class": 'btn-success btn-xs',
                awToolTip: 'Relaunch the job template, running it again from scratch'
                },
            cancel: {
                label: 'Cancel',
                icon: 'icon-minus-sign',
                mode: 'all',
                ngClick: 'deleteJob(\{\{ job.id \}\})',
                "class": 'btn-danger btn-xs delete-btn',
                awToolTip: 'Cancel a running or pending job',
                ngShow: "job.status == 'pending' || job.status == 'running' || job.status == 'waiting'"
                },
            "delete": {
                label: 'Delete',
                icon: 'icon-trash',
                mode: 'all',
                ngClick: 'deleteJob(\{\{ job.id \}\})',
                "class": 'btn-danger btn-xs delete-btn',
                awToolTip: 'Remove the selected job from the database',
                ngShow: "job.status != 'pending' && job.status != 'running' && job.status != 'waiting'"
                },
             dropdown: {
                type: 'DropDown',
                label: 'View',
                icon: 'icon-zoom-in',
                'class': 'btn-default btn-xs',
                options: [
                    { ngClick: "editJob(\{\{ job.id \}\}, '\{\{ job.summary_fields.job_template.name \}\}')", label: 'Status' },
                    { ngClick: "viewEvents(\{{ job.id \}\}, '\{\{ job.summary_fields.job_template.name \}\}')", label: 'Events',
                        ngHide: "job.status == 'new'" },
                    { ngClick: "viewSummary(\{{ job.id \}\}, '\{\{ job.summary_fields.job_template.name \}\}')", label: 'Host Summary', 
                        ngHide: "job.status == 'new'" }
                    ]
                },
            }
        });
