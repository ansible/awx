/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default ['i18n', function(i18n) {
    return {

        name: 'schedules',
        iterator: 'schedule',
        editTitle: i18n._('SCHEDULED JOBS'),
        hover: true,
        well: false,
        emptyListText: i18n._('No schedules exist'),

        fields: {
            enabled: {
                label: '',
                columnClass: 'List-staticColumn--toggle',
                type: 'toggle',
                ngClick: "toggleSchedule($event, schedule.id)",
                nosort: true,
                awToolTip: "{{ schedule.play_tip }}",
                ngDisabled: "!schedule.summary_fields.user_capabilities.edit",
                dataTipWatch: "schedule.play_tip",
                dataPlacement: 'top'
            },
            name: {
                label: i18n._('Name'),
                columnClass: 'col-lg-4 col-md-5 col-sm-5 col-xs-7 List-staticColumnAdjacent',
                sourceModel: 'unified_job_template',
                sourceField: 'name',
                // ngBind: 'schedule.summary_fields.unified_job_template.name',
                ngClick: "editSchedule(schedule)",
                awToolTip: "{{ schedule.nameTip | sanitize}}",
                dataTipWatch: 'schedule.nameTip',
                dataPlacement: "top",
            },
            type: {
                label: i18n._('Type'),
                noLink: true,
                columnClass: "col-lg-2 col-md-2 hidden-sm hidden-xs",
                sourceModel: 'unified_job_template',
                sourceField: 'unified_job_type',
                ngBind: 'schedule.type_label',
                searchField: 'unified_job_template__polymorphic_ctype__model'
            },
            next_run: {
                label: i18n._('Next Run'),
                noLink: true,
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
                awToolTip: i18n._("Edit the schedule"),
                dataPlacement: "top",
                ngShow: 'schedule.summary_fields.user_capabilities.edit'
            },
            "view": {
                mode: "all",
                ngClick: "editSchedule(schedule)",
                awToolTip: i18n._("View the schedule"),
                dataPlacement: "top",
                ngShow: '!schedule.summary_fields.user_capabilities.edit'
            },
            "delete": {
                mode: 'all',
                ngClick: 'deleteSchedule(schedule.id)',
                awToolTip: i18n._('Delete the schedule'),
                dataPlacement: 'top',
                ngShow: 'schedule.summary_fields.user_capabilities.delete'
            }
        }
    };}];
