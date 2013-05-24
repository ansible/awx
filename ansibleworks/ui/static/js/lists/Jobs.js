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
                label: 'Refresh',
                class: 'btn-success btn-small',
                ngClick: "refreshJob(\{\{ job.id \}\})",
                icon: 'icon-refresh',
                awToolTip: 'Refresh the page',
                mode: 'all'
                }
            },

        fieldActions: {
            edit: {
                icon: 'icon-edit',
                label: 'Edit',
                ngClick: "editJob(\{\{ job.id \}\}, '\{\{ job.name \}\}')",
                class: 'btn-success btn-small',
                awToolTip: 'Edit job details',
                },
            summary: {
                label: 'Hosts',
                icon: 'icon-th-large',
                ngClick: "viewSummary(\{{ job.id \}\}, '\{\{ job.name \}\}')",
                class: 'btn-info btn-small',
                awToolTip: 'View host summary',
                ngDisabled: "job.status == 'new'"
                },
            events: {
                label: 'Events',
                icon: 'icon-list-ul',
                mode: 'all',             
                ngClick: "viewEvents(\{{ job.id \}\}, '\{\{ job.name \}\}')",
                class: 'btn-info btn-small',
                awToolTip: 'View events',
                ngDisabled: "job.status == 'new'"
                },
            cancel: {
                icon: 'icon-minus-sign',
                label: 'Cancel',
                mode: 'all',             
                ngClick: 'deleteJob(\{\{ job.id \}\})',
                class: 'btn-danger btn-small',
                awToolTip: 'Cancel job',
                ngDisabled: "job.status != 'new' && job.status != 'pending' && job.status != 'running'"
                }
            }
        });
