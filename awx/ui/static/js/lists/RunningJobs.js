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
        'class': 'table-condensed',
        index: false,
        hover: true,
        well: false,
        
        fields: {
            id: {
                label: 'Job ID',
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
                label: 'Last Updated',
                link: false,
                searchable: false,
                filter: "date:'MM/dd/yy HH:mm:ss'",
                columnClass: "col-md-2 hidden-xs"
            },
            next_job_run: {
                label: 'Next Run',
                searchable: false,
                filter: "date:'MM/dd/yy HH:mm:ss'",
                columnClass: "col-md-2 hidden-sm hidden-xs"
            },
            type: {
                label: 'Type',
                link: false,
                columnClass: "col-md-2 hidden-sm hidden-xs"
            },
            name: {
                label: 'Name',
                columnClass: 'col-md-3 col-xs-5',
                ngHref: 'nameHref',
                sourceModel: 'template',
                sourceField: 'name'
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
                awToolTip: "{{ running_job.status_tip }}",
                awTipPlacement: "top",
                dataTitle: "{{ running_job.status_popover_title }}",
                iconClass: 'fa icon-job-{{ running_job.status }}',
                awPopOver: "{{ running_job.status_popover }}",
                dataPlacement: 'left'
            },
            submit: {
                icon: 'icon-rocket',
                mode: 'all',
                ngClick: 'submitJob(running_job.id, running_job.summary_fields.job_template.name)',
                awToolTip: 'Launch another instance of the job',
                dataPlacement: 'top'
            },
            cancel: {
                mode: 'all',
                ngClick: 'deleteJob(running_job.id)',
                awToolTip: 'Cancel the job',
                dataPlacement: 'top'
            },
            dropdown: {
                type: 'DropDown',
                label: 'View',
                icon: 'fa-search-plus',
                'class': 'btn-default btn-xs',
                options: [
                    { ngHref: '/#/jobs/{{ running_job.id }}', label: 'Status' },
                    { ngHref: '/#/jobs/{{ running_job.id }}/job_events', label: 'Events' },
                    { ngHref: '/#/jobs/{{ running_job.id }}/job_host_summaries', label: 'Host Summary' }
                ]
            }
        }
    });
