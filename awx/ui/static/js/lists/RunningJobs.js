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
                ngClick:"viewJobLog(running_job.id)",
                key: true,
                desc: true,
                searchType: 'int',
                columnClass: 'col-md-1 col-sm-2 col-xs-2',
                awToolTip: "{{ running_job.status_tip }}",
                awTipPlacement: "top",
            },
            status: {
                label: 'Status',
                columnClass: 'col-md-2 col-sm-2 col-xs-2',
                awToolTip: "{{ running_job.status_tip }}",
                awTipPlacement: "top",
                dataTitle: "{{ running_job.status_popover_title }}",
                icon: 'icon-job-{{ running_job.status }}',
                iconOnly: true,
                ngClick:"viewJobLog(running_job.id)",
                searchable: false
            },
            started: {
                label: 'Started On',
                noLink: true,
                searchable: false,
                filter: "date:'MM/dd HH:mm:ss'",
                columnClass: "col-md-2 hidden-xs"
            },
            type: {
                label: 'Type',
                ngBind: 'running_job.type_label',
                link: false,
                columnClass: "col-md-2 hidden-sm hidden-xs",
                searchable: true,
                searchType: 'select',
                searchOptions: []    // populated via GetChoices() in controller
            },
            name: {
                label: 'Name',
                columnClass: 'col-md-3 col-xs-5',
                ngClick: "viewJobLog(running_job.id, running_job.nameHref)",
                defaultSearchField: true
            }
        },

        actions: { },
       
        fieldActions: {
            submit: {
                icon: 'icon-rocket',
                mode: 'all',
                ngClick: 'relaunchJob($event, running_job.id)',
                awToolTip: 'Relaunch using the same parameters',
                dataPlacement: 'top'
            },
            cancel: {
                mode: 'all',
                ngClick: 'deleteJob(running_job.id)',
                awToolTip: 'Cancel the job',
                dataPlacement: 'top'
            },
            job_details: {
                mode: 'all',
                href: '/#/jobs/{{ running_job.id }}',
                awToolTip: 'View job details',
                dataPlacement: 'top'
            },
            stdout: {
                mode: 'all',
                href: '/#/jobs/{{ running_job.id }}/stdout',
                awToolTip: 'View standard output. Opens in a new window or tab.',
                dataPlacement: 'top'
            }
            /*dropdown: {
                type: 'DropDown',
                ngShow: "running_job.type === 'job'",
                label: 'View',
                icon: 'fa-search-plus',
                'class': 'btn-default btn-xs',
                options: [
                    //{ ngHref: '/#/jobs/{{ running_job.id }}', label: 'Status' },
                    { ngHref: '/#/job_events/{{ running_job.id }}', label: 'Events' },
                    { ngHref: '/#/job_host_summaries/{{ running_job.id }}', label: 'Host Summary' }
                ]
            }*/
        }
    });
