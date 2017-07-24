/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default ['i18n', function(i18n) {
    return {

        name: 'schedules',
        iterator: 'schedule',
        selectTitle: '',
        editTitle: 'SCHEDULES',
        listTitle: '{{parentObject | sanitize}} || SCHEDULES',
        index: false,
        hover: true,

        fields: {
            toggleSchedule: {
                ngDisabled: "!schedule.summary_fields.user_capabilities.edit",
                label: '',
                columnClass: 'List-staticColumn--toggle',
                type: "toggle",
                ngClick: "toggleSchedule($event, schedule.id)",
                awToolTip: "{{ schedule.play_tip }}",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: "right",
                nosort: true,
            },
            name: {
                key: true,
                label: i18n._('Name'),
                ngClick: "editSchedule(schedule)",
                columnClass: "col-md-3 col-sm-3 col-xs-6"
            },
            dtstart: {
                label: i18n._('First Run'),
                filter: "longDate",
                columnClass: "List-staticColumn--schedulerTime hidden-sm hidden-xs"
            },
            next_run: {
                label: i18n._('Next Run'),
                filter: "longDate",
                columnClass: "List-staticColumn--schedulerTime hidden-xs"
            },
            dtend: {
                label: i18n._('Final Run'),
                filter: "longDate",
                columnClass: "List-staticColumn--schedulerTime hidden-xs"
            },
        },

        actions: {
            refresh: {
                mode: 'all',
                awToolTip: i18n._("Refresh the page"),
                ngClick: "refreshSchedules()",
                actionClass: 'btn List-buttonDefault',
                ngShow: "socketStatus == 'error'",
                buttonContent: i18n._('REFRESH')
            },
            add: {
                mode: 'all',
                ngClick: 'addSchedule()',
                awToolTip: i18n._('Add a new schedule'),
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ' + i18n._('ADD'),
                ngShow: 'canAdd'
            }
        },

        fieldActions: {
            edit: {
                label: i18n._('Edit'),
                ngClick: "editSchedule(schedule)",
                icon: 'icon-edit',
                awToolTip: i18n._('Edit schedule'),
                dataPlacement: 'top',
                ngShow: 'schedule.summary_fields.user_capabilities.edit'
            },
            view: {
                label: i18n._('View'),
                ngClick: "editSchedule(schedule)",
                awToolTip: i18n._('View schedule'),
                dataPlacement: 'top',
                ngShow: '!schedule.summary_fields.user_capabilities.edit'
            },
            "delete": {
                label: i18n._('Delete'),
                ngClick: "deleteSchedule(schedule.id)",
                icon: 'icon-trash',
                awToolTip: i18n._('Delete schedule'),
                dataPlacement: 'top',
                ngShow: 'schedule.summary_fields.user_capabilities.delete'
            }
        }
    };}];
