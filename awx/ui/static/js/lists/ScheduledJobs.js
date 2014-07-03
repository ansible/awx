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
        index: true,
        hover: true,
        well: false,

        fields: {
            status: {
                label: 'Status',
                columnClass: 'col-lg-1 col-md-2 col-sm-2 col-xs-2',
                awToolTip: "{{ schedule.status_tip }}",
                awTipPlacement: "top",
                icon: 'icon-job-{{ schedule.status }}',
                iconOnly: true,
                ngClick: "toggleSchedule($event, schedule.id)",
                searchable: false,
                nosort: true
            },
            next_run: {
                label: 'Next Run',
                noLink: true,
                searchable: false,
                columnClass: "col-lg-2 col-md-2 hidden-xs",
                filter: "date:'MM/dd HH:mm:ss'",
                key: true
            },
            type: {
                label: 'Type',
                noLink: true,
                columnClass: "col-lg-2 col-md-2 hidden-sm hidden-xs",
                sourceModel: 'unified_job_template',
                sourceField: 'unified_job_type',
                ngBind: 'schedule.type_label',
                searchable: false,
                nosort: true
            },
            name: {
                label: 'Name',
                columnClass: 'col-md-3 col-sm-4 col-xs-4',
                sourceModel: 'unified_job_template',
                sourceField: 'name',
                ngClick: "editSchedule(schedule.id)",
                awToolTip: "{{ schedule.nameTip }}",
                dataPlacement: "top",
                defaultSearchField: true
            }
        },

        actions: { },

        fieldActions: {
            "play": {
                mode: "all",
                ngClick: "toggleSchedule($event, schedule.id)",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                iconClass: "{{ 'fa icon-schedule-enabled-' + schedule.enabled }}",
                dataPlacement: 'top'
            },
            "edit": {
                mode: "all",
                ngClick: "editSchedule(schedule.id)",
                awToolTip: "Edit the schedule",
                dataPlacement: "top"
            },
            "delete": {
                mode: 'all',
                ngClick: 'deleteSchedule(schedule.id)',
                awToolTip: 'Delete the schedule',
                dataPlacement: 'top'
            }
        }
    });