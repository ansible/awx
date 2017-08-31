/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {

        name: 'projects',
        iterator: 'project',
        basePath: 'projects',
        selectTitle: i18n._('Add Project'),
        editTitle: i18n._('PROJECTS'),
        listTitle: i18n._('PROJECTS'),
        selectInstructions: '<p>Select existing projects by clicking each project or checking the related checkbox. When finished, click the blue ' +
            '<em>Select</em> button, located bottom right.</p><p>Create a new project by clicking the <i class=\"fa fa-plus\"></i> button.</p>',
        index: false,
        hover: true,
        emptyListText: i18n._('No Projects Have Been Created'),

        fields: {
            status: {
                label: '',
                iconOnly: true,
                ngClick: 'showSCMStatus(project.id)',
                awToolTip: '{{ project.statusTip }}',
                dataTipWatch: 'project.statusTip',
                dataPlacement: 'right',
                icon: "icon-job-{{ project.statusIcon }}",
                columnClass: "List-staticColumn--smallStatus",
                nosort: true,
                excludeModal: true
            },
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: "col-lg-4 col-md-4 col-sm-5 col-xs-7 List-staticColumnAdjacent",
                modalColumnClass: 'col-md-8',
                awToolTip: '{{project.description | sanitize}}',
                dataPlacement: 'top'
            },
            scm_type: {
                label: i18n._('Type'),
                ngBind: 'project.type_label',
                excludeModal: true,
                columnClass: 'col-lg-2 col-md-2 col-sm-3 hidden-xs'
            },
            scm_revision: {
                label: i18n._('Revision'),
                excludeModal: true,
                columnClass: 'List-tableCell col-lg-4 col-md-2 col-sm-3 hidden-xs',
                type: 'revision'
            },
            last_updated: {
                label: i18n._('Last Updated'),
                filter: "longDate",
                columnClass: "col-lg-3 col-md-3 hidden-sm hidden-xs",
                excludeModal: true,
                nosort: true
            }
        },

        actions: {
            refresh: {
                mode: 'all',
                awToolTip: i18n._("Refresh the page"),
                ngClick: "refresh()",
                ngShow: "socketStatus === 'error'",
                actionClass: 'btn List-buttonDefault',
                buttonContent: i18n._('REFRESH')
            },
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addProject()',
                awToolTip: i18n._('Create a new project'),
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ' + i18n._('ADD'),
                ngShow: "canAdd"
            }
        },

        fieldActions: {

            columnClass: 'col-lg-2 col-md-3 col-sm-4 col-xs-5',

            scm_update: {
                ngClick: 'SCMUpdate(project.id, $event)',
                awToolTip: "{{ project.scm_update_tooltip }}",
                dataTipWatch: "project.scm_update_tooltip",
                ngClass: "project.scm_type_class",
                dataPlacement: 'top',
                ngShow: "project.summary_fields.user_capabilities.start"
            },
            schedule: {
                mode: 'all',
                ngClick: "editSchedules(project.id)",
                awToolTip: "{{ project.scm_schedule_tooltip }}",
                ngClass: "project.scm_type_class",
                dataPlacement: 'top',
                ngShow: "project.summary_fields.user_capabilities.schedule"
            },
            edit: {
                ngClick: "editProject(project.id)",
                awToolTip: i18n._('Edit the project'),
                dataPlacement: 'top',
                ngShow: "project.summary_fields.user_capabilities.edit"
            },
            view: {
                ngClick: "editProject(project.id)",
                awToolTip: i18n._('View the project'),
                dataPlacement: 'top',
                ngShow: "!project.summary_fields.user_capabilities.edit",
                icon: 'fa-eye',
            },
            "delete": {
                ngClick: "deleteProject(project.id, project.name)",
                awToolTip: i18n._('Delete the project'),
                ngShow: "(project.status !== 'updating' && project.status !== 'running' && project.status !== 'pending' && project.status !== 'waiting')  && project.summary_fields.user_capabilities.delete",
                dataPlacement: 'top'
            },
            cancel: {
                ngClick: "cancelUpdate(project)",
                awToolTip: i18n._('Cancel the SCM update'),
                ngShow: "(project.status == 'updating' || project.status == 'running' || project.status == 'pending' || project.status == 'waiting') && project.summary_fields.user_capabilities.start",
                dataPlacement: 'top',
                ngDisabled: "project.pending_cancellation || project.status == 'canceled'"
            }
        }
    };}];
