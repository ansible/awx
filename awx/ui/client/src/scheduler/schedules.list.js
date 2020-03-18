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
        layoutClass: 'List-staticColumnLayout--schedules',
        staticColumns: [
            {
                field: 'invalid',
                content: {
                    label: '',
                    type: 'invalid',
                    nosort: true,
                    awToolTip: i18n._("Resources are missing from this template."),
                    dataPlacement: 'right',
                    ngShow: '!isValid(schedule)'
                }
            },
            {
                field: 'toggleSchedule',
                content: {
                    ngDisabled: "!schedule.summary_fields.user_capabilities.edit || credentialRequiresPassword",
                    label: '',
                    type: "toggle",
                    ngClick: "toggleSchedule($event, schedule.id)",
                    awToolTip: "{{ schedule.play_tip }}",
                    dataTipWatch: "schedule.play_tip",
                    dataPlacement: "right",
                    nosort: true,
                }
            }
        ],

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                uiSref: "{{schedule.linkToDetails}}",
                columnClass: "col-sm-3 col-xs-6"
            },
            dtstart: {
                label: i18n._('First Run'),
                filter: "longDate",
                columnClass: "d-none d-sm-flex col-sm-2"
            },
            next_run: {
                label: i18n._('Next Run'),
                filter: "longDate",
                columnClass: "d-none d-sm-flex col-sm-2"
            },
            dtend: {
                label: i18n._('Final Run'),
                filter: "longDate",
                columnClass: "d-none d-sm-flex col-sm-2"
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
                ngClick: 'credentialRequiresPassword || addSchedule()',
                awToolTip: i18n._('Add a new schedule'),
                dataTipWatch: 'addTooltip',
                actionClass: 'at-Button--add',
                actionId: 'button-add--schedule',
                ngShow: 'canAdd',
                ngClass: "{ 'Form-tab--disabled': credentialRequiresPassword }"
            }
        },

        fieldActions: {
            columnClass: 'col-sm-3 col-xs-6',
            edit: {
                label: i18n._('Edit'),
                ngClick: "editSchedule(schedule)",
                icon: 'icon-edit',
                awToolTip: i18n._('Edit schedule'),
                dataPlacement: 'top',
                ngShow: 'schedule.summary_fields.user_capabilities.edit && !credentialRequiresPassword'
            },
            view: {
                label: i18n._('View'),
                ngClick: "editSchedule(schedule)",
                awToolTip: i18n._('View schedule'),
                dataPlacement: 'top',
                ngShow: '!schedule.summary_fields.user_capabilities.edit || credentialRequiresPassword'
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
