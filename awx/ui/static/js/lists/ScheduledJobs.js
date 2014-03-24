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
        
        name: 'scheduled_jobs',
        iterator: 'scheduled_job',
        editTitle: 'Scheduled Jobs',
        'class': 'table-condensed',
        index: false,
        hover: true,
        well: false,
        
        fields: {
            next_run: {
                label: 'Next Run',
                link: false,
                columnClass: "col-md-2"
            },
            dtend: {
                label: 'Ends On',
                searchable: false,
                filter: "date:'MM/dd/yy HH:mm:ss'",
                columnClass: "col-md-2 hidden-xs"
            },
            type: {
                label: 'Type',
                link: false,
                columnClass: "col-md-2 hidden-sm hidden-xs"
            },
            template_name: {
                label: 'Name',
                columnClass: "col-md-4 col-xs-5",
                sourceModel: "template",
                sourceField: "name"
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
            "play": {
                mode: "all",
                ngClick: "toggleSchedule(scheduled_job.id)",
                awToolTip: "{{ scheduled_job.play_tip }}",
                dataTipWatch: "scheduled_job.play_tip",
                iconClass: "{{ 'fa icon-schedule-enabled-' + scheduled_job.enabled }}",
                dataPlacement: 'top',
            },
            "edit": {
                mode: "all",
                ngClick: "edit(scheduled_job.id)",
                awToolTip: "Edit the schedule",
                dataPlacement: "top"
            },
            "delete": {
                mode: 'all',
                ngClick: 'deleteJob(completed_job.id)',
                awToolTip: 'Delete the schedule',
                dataPlacement: 'top'
            }
        }
    });