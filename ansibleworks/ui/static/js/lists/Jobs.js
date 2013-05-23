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
        class: 'jobs-table',
        
        fields: {
            id: {
                label: 'Job ID',
                key: true,
                desc: true,
                searchType: 'int'   
                },
            name: {
                label: 'Name',
                link: true,
                },
            created: {
                label: 'Creation Date',
                link: true
                },
            status: {
                label: 'Status',
                icon: 'icon-circle',
                class: 'job-\{\{ job.status \}\}',
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
                ngClick: "refreshJob(\{\{ job.id \}\})",
                icon: 'icon-refresh',
                awToolTip: 'Refresh the page',
                mode: 'all'
                }
            },

        fieldActions: {
            edit: {
                ngClick: "editJob(\{\{ job.id \}\}, '\{\{ job.name \}\}')",
                icon: 'icon-edit',
                class: 'btn-mini',
                awToolTip: 'View/Edit detail',
                },
            summary: {
                title: 'Summary',
                icon: 'icon-filter',
                ngClick: "viewSummary(\{{ job.id \}\}, '\{\{ job.name \}\}')",
                class: 'btn-success btn-mini',
                awToolTip: 'View host summary',
                ngDisabled: "job.status == 'new'"
                },
            events: {
                title: 'Detail',
                icon: 'icon-list-ul',
                mode: 'all',             
                ngClick: "viewEvents(\{{ job.id \}\}, '\{\{ job.name \}\}')",
                class: 'btn-success btn-mini',
                awToolTip: 'View events',
                ngDisabled: "job.status == 'new'"
                },
            cancel: {
                title: 'Cancel',
                icon: 'icon-minus-sign',
                mode: 'all',             
                ngClick: 'deleteJob(\{\{ job.id \}\})',
                class: 'btn-danger btn-mini',
                awToolTip: 'Cancel job',
                ngDisabled: "job.status != 'new' && job.status != 'pending'"
                }
            }
        });
