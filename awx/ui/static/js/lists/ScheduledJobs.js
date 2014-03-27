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
        index: true,
        hover: true,
        well: false,
        
        fields: {
            next_run: {
                label: 'Next Run',
                link: false,
                searchable: false,
                columnClass: "col-md-2 hidden-xs",
                key: true,
                desc: true
            },
            type: {
                label: 'Type',
                link: false,
                columnClass: "col-md-2 hidden-sm hidden-xs"
            },
            template_name: {
                label: 'Name',
                columnClass: "col-md-3 col-xs-5",
                sourceModel: "template",
                sourceField: "name"
            }
            /*,
            dtend: {
                label: 'Ends On',
                searchable: false,
                filter: "date:'MM/dd/yy HH:mm:ss'",
                columnClass: "col-md-2 hidden-xs"
            }*/
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