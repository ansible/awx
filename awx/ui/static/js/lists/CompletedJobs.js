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
                linkTo: '/#/jobs/{{ completed_job.id }}',
                key: true,
                desc: true,
                searchType: 'int',
                columnClass: 'col-md-1 col-sm-2 col-xs-2'
            },
            inventory: {
                label: 'Inventory ID',
                searchType: 'int',
                searchOnly: true
            },
            modified: {
                label: 'Completed On',
                link: false,
                searchable: false,
                filter: "date:'MM/dd/yy HH:mm:ss'",
                columnClass: "col-md-2 hidden-xs"
            },
            type: {
                label: 'Type',
                ngBind: 'completed_job.type_label',
                link: false,
                columnClass: "col-md-2 hidden-sm hidden-xs"
            },
            name: {
                label: 'Name',
                columnClass: 'col-md-3 col-xs-5',
                ngHref: 'nameHref',
                sourceModel: 'template',
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
                searchType: 'select',
                searchOnly: true,
                searchOptions: [
                    { name: "Success", value: "successful" },
                    { name: "Error", value: "error" },
                    { name: "Failed", value: "failed" },
                    { name: "Canceled", value: "canceled" }
                ]
            }
        },

        actions: {
            columnClass: 'col-md-2 col-sm-3 col-xs-3',
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refresh()"
            }
        },
        
        fieldActions: {
            status: {
                mode: 'all',
                awToolTip: "{{ completed_job.status_tip }}",
                awTipPlacement: "top",
                dataTitle: "{{ completed_job.status_popover_title }}",
                iconClass: 'fa icon-job-{{ completed_job.status }}',
                awPopOver: "{{ completed_job.status_popover }}",
                dataPlacement: 'left'
            },
            submit: {
                icon: 'icon-rocket',
                mode: 'all',
                ngClick: 'relaunch(completed_job.id)',
                awToolTip: 'Relaunch the job',
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
                label: 'View',
                icon: 'fa-search-plus',
                'class': 'btn-default btn-xs',
                options: [
                    { ngHref: '/#/jobs/{{ completed_job.id }}', label: 'Status' },
                    { ngHref: '/#/jobs/{{ completed_job.id }}/job_events', label: 'Events', ngHide: "completed_job.status == 'new'" },
                    { ngHref: '/#/jobs/{{ completed_job.id }}/job_host_summaries', label: 'Host Summary' }
                ]
            }
        }
    });
