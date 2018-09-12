/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default ['i18n', function(i18n) {
    return {

        name: 'teams',
        iterator: 'team',
        selectTitle: i18n._('Add Team'),
        editTitle: i18n._('TEAMS'),
        listTitle: i18n._('TEAMS'),
        selectInstructions: i18n.sprintf(i18n._("Click on a row to select it, and click Finished when done. Click the %s button to create a new team."), "<i class=\"icon-plus\"></i> "),
        index: false,
        hover: true,

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-4 col-sm-9 col-xs-9',
                modalColumnClass: 'col-md-8',
                awToolTip: '{{team.description | sanitize}}',
                dataPlacement: 'top'
            },
            organization: {
                label: i18n._('Organization'),
                ngBind: 'team.summary_fields.organization.name',
                sourceModel: 'organization',
                sourceField: 'name',
                columnClass: 'd-none d-md-flex col-md-4',
                excludeModal: true
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addTeam()',
                awToolTip: i18n._('Create a new team'),
                actionClass: 'at-Button--add',
                actionId: 'button-add',
                ngShow: 'canAdd && canEdit'
            }
        },

        fieldActions: {

            columnClass: 'col-md-4 col-sm-3 col-xs-3',

            edit: {
                label: i18n._('Edit'),
                ngClick: "editTeam(team.id)",
                icon: 'icon-edit',
                "class": 'btn-xs btn-default',
                awToolTip: i18n._('Edit team'),
                dataPlacement: 'top',
                ngShow: 'team.summary_fields.user_capabilities.edit'
            },
            view: {
                label: i18n._('View'),
                ngClick: "editTeam(team.id)",
                "class": 'btn-xs btn-default',
                awToolTip: i18n._('View team'),
                dataPlacement: 'top',
                ngShow: '!team.summary_fields.user_capabilities.edit'
            },
            "delete": {
                label: i18n._('Delete'),
                ngClick: "deleteTeam(team.id, team.name)",
                icon: 'icon-trash',
                "class": 'btn-xs btn-danger',
                awToolTip: i18n._('Delete team'),
                dataPlacement: 'top',
                ngShow: 'team.summary_fields.user_capabilities.delete'
            }
        }
    };}];
