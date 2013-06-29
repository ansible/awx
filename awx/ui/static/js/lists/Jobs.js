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
            name: {
                label: 'Name',
                link: true
                },
            created: {
                label: 'Date',
                link: true,
                searchable: false
                },
            status: {
                label: 'Status',
                icon: 'icon-circle',
                "class": 'job-\{\{ job.status \}\}',
                searchType: 'select',
                searchOptions: [
                    { name: "new", value: "new" }, 
                    { name: "pending", value: "pending" },
                    { name: "running", value: "running" }, 
                    { name: "successful", value: "successful" },
                    { name: "error", value: "error" },
                    { name: "failed", value: "failed" },
                    { name: "canceled", value: "canceled" } ]
                }
            },
        
        actions: {
            refresh: {
                label: 'Refresh',
                "class": 'btn-success btn-small',
                ngClick: "refreshJob(\{\{ job.id \}\})",
                icon: 'icon-refresh',
                awToolTip: 'Refresh the page',
                mode: 'all'
                }
            },

        fieldActions: {
            summary: {
                label: 'Hosts',
                icon: 'icon-th-large',
                ngClick: "viewSummary(\{{ job.id \}\}, '\{\{ job.name \}\}')",
                "class": 'btn btn-small',
                awToolTip: 'View host summary',
                ngDisabled: "job.status == 'new'"
                },
            events: {
                label: 'Events',
                icon: 'icon-list-ul',
                mode: 'all',             
                ngClick: "viewEvents(\{{ job.id \}\}, '\{\{ job.name \}\}')",
                "class": 'btn btn-small',
                awToolTip: 'View events',
                ngDisabled: "job.status == 'new'"
                },
            edit: {
                label: 'Details',
                icon: 'icon-zoom-in',
                ngClick: "editJob(\{\{ job.id \}\}, '\{\{ job.name \}\}')",
                "class": 'btn btn-small',
                awToolTip: 'View job details'
                },
            rerun: {
                icon: 'icon-retweet',
                mode: 'all',             
                ngClick: "submitJob(\{\{ job.id \}\}, '\{\{ job.summary_fields.job_template.name \}\}' )",
                "class": 'btn-success btn-small',
                awToolTip: 'Re-run this job'
                },
            cancel: {
                icon: 'icon-minus-sign',
                mode: 'all',
                ngClick: 'deleteJob(\{\{ job.id \}\})',
                "class": 'btn-danger btn-small',
                awToolTip: 'Cancel job',
                ngDisabled: "job.status != 'new' && job.status != 'pending' && job.status != 'running'"
                }
            }
        });
