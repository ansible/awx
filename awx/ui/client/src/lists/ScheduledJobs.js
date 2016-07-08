/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('ScheduledJobsDefinition', ['sanitizeFilter'])
    .value( 'ScheduledJobsList', {

        name: 'schedules',
        iterator: 'schedule',
        editTitle: 'Scheduled Jobs',
        hover: true,
        well: false,
        emptyListText: 'No schedules exist',

        fields: {
            enabled: {
                label: '',
                columnClass: 'List-staticColumn--toggle',
                type: 'toggle',
                ngClick: "toggleSchedule($event, schedule.id)",
                searchable: false,
                nosort: true,
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: 'top'
            },
            name: {
                label: 'Name',
                columnClass: 'col-lg-4 col-md-5 col-sm-5 col-xs-7 List-staticColumnAdjacent',
                sourceModel: 'unified_job_template',
                sourceField: 'name',
                ngClick: "editSchedule(schedule)",
                awToolTip: "{{ schedule.nameTip | sanitize}}",
                dataPlacement: "top",
                defaultSearchField: true
            },
            type: {
                label: 'Type',
                noLink: true,
                columnClass: "col-lg-2 col-md-2 hidden-sm hidden-xs",
                sourceModel: 'unified_job_template',
                sourceField: 'unified_job_type',
                ngBind: 'schedule.type_label',
                searchField: 'unified_job_template__name',
                searchLable: 'Type',
                searchable: true,
                searchType: 'select',
                searchOptions: [
                    { value: 'inventory source', label: 'Inventory Sync' },
                    { value: 'job template', label: 'Playbook Run' },
                    { value: 'project', label: 'SCM Update' }
                ]
            },
            next_run: {
                label: 'Next Run',
                noLink: true,
                searchable: false,
                columnClass: "col-lg-3 col-md-2 col-sm-3 hidden-xs",
                filter: "longDate",
                key: true
            }
        },

        actions: { },

        fieldActions: {

            columnClass: 'col-lg-3 col-md-3 col-sm-3 col-xs-5',
            "edit": {
                mode: "all",
                ngClick: "editSchedule(schedule)",
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
