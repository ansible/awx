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
        layoutClass: 'List-staticColumnLayout--statusOrCheckbox',
        staticColumns: [
            {
                field: 'status',
                content: {
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
                }
            }
        ],

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: "col-md-3 col-sm-6 List-staticColumnAdjacent",
                modalColumnClass: 'col-md-8',
                awToolTip: '{{project.description | sanitize}}',
                dataPlacement: 'top'
            },
            scm_type: {
                label: i18n._('Type'),
                ngBind: 'project.type_label',
                excludeModal: true,
                columnClass: 'col-md-2 col-sm-2'
            },
            scm_revision: {
                label: i18n._('Revision'),
                excludeModal: true,
                columnClass: 'd-none d-md-flex col-md-2',
                type: 'revision'
            },
            last_updated: {
                label: i18n._('Last Updated'),
                filter: "longDate",
                columnClass: "d-none d-md-flex col-md-2",
                excludeModal: true
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
                actionClass: 'at-Button--add',
                actionId: 'button-add',
                ngShow: "canAdd"
            }
        },

        fieldActions: {

            columnClass: 'col-md-3 col-sm-4',
            edit: {
                ngClick: "editProject(project.id)",
                awToolTip: i18n._('Edit the project'),
                dataPlacement: 'top',
                ngShow: "project.summary_fields.user_capabilities.edit"
            },
            scm_update: {
                ngClick: 'SCMUpdate(project.id, $event)',
                awToolTip: "{{ project.scm_update_tooltip }}",
                dataTipWatch: "project.scm_update_tooltip",
                ngClass: "project.scm_type_class",
                dataPlacement: 'top',
                ngShow: "project.summary_fields.user_capabilities.start"
            },
            copy: {
                label: i18n._('Copy'),
                ngClick: 'copyProject(project)',
                "class": 'btn-danger btn-xs',
                awToolTip: i18n._('Copy project'),
                dataPlacement: 'top',
                ngShow: 'project.summary_fields.user_capabilities.copy'
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
