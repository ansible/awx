/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('TeamsListDefinition', [])
    .value('TeamList', {

        name: 'teams',
        iterator: 'team',
        selectTitle: 'Add Team',
        editTitle: 'Teams',
        listTitle: 'Teams',
        selectInstructions: "Click on a row to select it, and click Finished when done. Click the <i class=\"icon-plus\"></i> " +
            "button to create a new team.",
        index: false,
        hover: true,

        fields: {
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-lg-3 col-md-4 col-sm-9 col-xs-9',
                modalColumnClass: 'col-md-8'
            },
            description: {
                label: 'Description',
                columnClass: 'col-lg-3 col-md-3 hidden-sm hidden-xs',
                excludeModal: true
            },
            organization: {
                label: 'Organization',
                ngBind: 'team.organization_name',
                sourceModel: 'organization',
                sourceField: 'name',
                columnClass: 'col-md-3 hidden-sm hidden-xs',
                excludeModal: true
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addTeam()',
                awToolTip: 'Create a new team',
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD',
                ngShow: 'canAdd'
            }
        },

        fieldActions: {

            columnClass: 'col-lg-3 col-md-2 col-sm-3 col-xs-3',

            edit: {
                label: 'Edit',
                ngClick: "editTeam(team.id)",
                icon: 'icon-edit',
                "class": 'btn-xs btn-default',
                awToolTip: 'Edit team',
                dataPlacement: 'top',
                ngShow: 'team.summary_fields.user_capabilities.edit'
            },
            view: {
                label: 'View',
                ngClick: "editTeam(team.id)",
                "class": 'btn-xs btn-default',
                awToolTip: 'View team',
                dataPlacement: 'top',
                ngShow: '!team.summary_fields.user_capabilities.edit'
            },
            "delete": {
                label: 'Delete',
                ngClick: "deleteTeam(team.id, team.name)",
                icon: 'icon-trash',
                "class": 'btn-xs btn-danger',
                awToolTip: 'Delete team',
                dataPlacement: 'top',
                ngShow: 'team.summary_fields.user_capabilities.delete'
            }
        }
    });
