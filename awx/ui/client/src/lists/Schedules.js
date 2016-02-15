/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('SchedulesListDefinition', [])
    .value('SchedulesList', {

        name: 'schedules',
        iterator: 'schedule',
        selectTitle: '',
        editTitle: 'Schedules',
        listTitle: 'Schedules',
        index: false,
        hover: true,

        fields: {
            toggleSchedule: {
                label: '',
                columnClass: 'List-staticColumn--toggle',
                type: "toggle",
                ngClick: "toggleSchedule($event, schedule.id)",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: "right",
                searchable: false,
                nosort: true,
            },
            name: {
                key: true,
                label: 'Name',
                ngClick: "editSchedule(schedule.id)",
                columnClass: "col-md-3 col-sm-3 col-xs-6"
            },
            dtstart: {
                label: 'First Run',
                filter: "longDate",
                searchable: false,
                columnClass: "List-staticColumn--schedulerTime hidden-sm hidden-xs"
            },
            next_run: {
                label: 'Next Run',
                filter: "longDate",
                searchable: false,
                columnClass: "List-staticColumn--schedulerTime hidden-xs"
            },
            dtend: {
                label: 'Final Run',
                filter: "longDate",
                searchable: false,
                columnClass: "List-staticColumn--schedulerTime hidden-xs"
            }
        },

        actions: {
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refreshSchedules()",
                actionClass: 'btn List-buttonDefault',
                ngShow: "socketStatus == 'error'",
                buttonContent: 'REFRESH'
            },
            add: {
                mode: 'all',
                ngClick: 'addSchedule()',
                awToolTip: 'Add a new schedule',
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD'
            }
        },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editSchedule(schedule.id)",
                icon: 'icon-edit',
                awToolTip: 'Edit schedule',
                dataPlacement: 'top'
            },
            "delete": {
                label: 'Delete',
                ngClick: "deleteSchedule(schedule.id)",
                icon: 'icon-trash',
                awToolTip: 'Delete schedule',
                dataPlacement: 'top'
            }
        }
    });
