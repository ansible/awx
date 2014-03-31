/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  ScheduledJobs.js 
 *
 * 
 */

'use strict';

angular.module('ScheduledJobsDefinition', [])
    .value( 'ScheduledJobsList', {
        
        name: 'schedules',
        iterator: 'schedule',
        editTitle: 'Scheduled Jobs',
        'class': 'table-condensed',
        index: true,
        hover: true,
        well: false,
        
        fields: {
            status: {
                label: 'Status',
                columnClass: 'col-md-2 col-sm-2 col-xs-2',
                awToolTip: "{{ scheduled_job.status_tip }}",
                awTipPlacement: "top",
                icon: 'icon-job-{{ scheduled_job.status }}',
                iconOnly: true,
                ngClick: "toggleSchedule(scheduled_job.id)"
            },
            next_run: {
                label: 'Next Run',
                link: false,
                searchable: false,
                columnClass: "col-md-2 hidden-xs",
                filter: "date:'MM/dd/yy HH:mm:ss'",
                key: true,
                desc: true
            },
            type: {
                label: 'Type',
                link: false,
                sourceModel: '',
                sourceField: '',
                columnClass: "col-md-2 hidden-sm hidden-xs"
            },
            name: {
                label: 'Name',
                columnClass: "col-md-3 col-xs-5",
            }
        },

        actions: {
            columnClass: 'col-md-2 col-sm-3 col-xs-3',
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refreshJobs()"
            }
        },
        
        fieldActions: {
            "play": {
                mode: "all",
                ngClick: "toggleSchedule($event, schedule.id)",
                awToolTip: "{{ scheduled_job.play_tip }}",
                dataTipWatch: "scheduled_job.play_tip",
                iconClass: "{{ 'fa icon-schedule-enabled-' + scheduled_job.enabled }}",
                dataPlacement: 'top'
            },
            "edit": {
                mode: "all",
                ngClick: "editSchedule(scheduled_job.id)",
                awToolTip: "Edit the schedule",
                dataPlacement: "top"
            },
            "delete": {
                mode: 'all',
                ngClick: 'deleteSchedule(scheduled_job.id)',
                awToolTip: 'Delete the schedule',
                dataPlacement: 'top'
            }
        }
    });