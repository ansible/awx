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
                desc: true    
                },
            created: {
                label: 'Creation Date',
                link: true
                },
            name: {
                label: 'Name',
                link: true,
                },
            status: {
                label: 'Status',
                icon: 'icon-circle',
                class: 'job-\{\{ job.status \}\}'
                }
            },
        
        actions: {
                },

        fieldActions: {
            edit: {
                ngClick: "editJob(\{\{ job.id \}\})",
                icon: 'icon-edit',
                class: 'btn-mini',
                awToolTip: 'Edit job',
                ngDisabled: "job.status != 'new'"
                },
            summary: {
                title: 'Summary',
                icon: 'icon-filter',
                ngClick: 'viewSummary()',
                class: 'btn-success btn-mini',
                awToolTip: 'Job summary',
                ngDisabled: "job.status == 'new'"
                },
            events: {
                title: 'Detail',
                icon: 'icon-list-ul',
                mode: 'all',             
                ngClick: 'viewEvents()',
                class: 'btn-info btn-mini',
                awToolTip: 'Job event detail',
                ngDisabled: "job.status == 'new'"
                },
            cancel: {
                title: 'Cancel',
                icon: 'icon-minus-sign',
                mode: 'all',             
                ngClick: 'cancel(\{\{ job.id \}\})',
                class: 'btn-danger btn-mini',
                awToolTip: 'Cancel job',
                ngDisabled: "job.status == 'error' || job.status == 'failed'"
                }
            }
        });
