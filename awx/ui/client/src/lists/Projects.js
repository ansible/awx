/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('ProjectsListDefinition', [])
    .value('ProjectList', {

        name: 'projects',
        iterator: 'project',
        selectTitle: 'Add Project',
        editTitle: 'Projects',
        listTitle: 'Projects',
        selectInstructions: '<p>Select existing projects by clicking each project or checking the related checkbox. When finished, click the blue ' +
            '<em>Select</em> button, located bottom right.</p><p>Create a new project by clicking the <i class=\"fa fa-plus\"></i> button.</p>',
        index: false,
        hover: true,

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
                searchLabel: 'Status',
                searchType: 'select',
                searchOptions: [],  //set in the controller
                excludeModal: true
            },
            name: {
                key: true,
                searchDefault: true,
                label: 'Name',
                columnClass: "col-lg-4 col-md-4 col-sm-5 col-xs-7 List-staticColumnAdjacent",
                modalColumnClass: 'col-md-8'
            },
            scm_type: {
                label: 'Type',
                searchType: 'select',
                searchOptions: [], // will be set by Options call to projects resource
                excludeModal: true,
                columnClass: 'col-lg-3 col-md-2 col-sm-3 hidden-xs'
            },
            last_updated: {
                label: 'Last Updated',
                filter: "longDate",
                columnClass: "col-lg-3 col-md-3 hidden-sm hidden-xs",
                excludeModal: true,
                searchable: false,
                nosort: true
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addProject()',
                awToolTip: 'Create a new project',
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD',
                ngShow: "canAdd"
            },
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refresh()",
                ngShow: "socketStatus == 'error'",
                actionClass: 'btn List-buttonDefault',
                buttonContent: 'REFRESH'
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
                awToolTip: 'Edit the project',
                dataPlacement: 'top',
                ngShow: "project.summary_fields.user_capabilities.edit"
            },
            view: {
                ngClick: "editProject(project.id)",
                awToolTip: 'View the project',
                dataPlacement: 'top',
                ngShow: "!project.summary_fields.user_capabilities.edit",
                icon: 'fa-eye',
            },
            "delete": {
                ngClick: "deleteProject(project.id, project.name)",
                awToolTip: 'Delete the project',
                ngShow: "(project.status !== 'updating' && project.status !== 'running' && project.status !== 'pending')  && project.summary_fields.user_capabilities.delete",
                dataPlacement: 'top'
            },
            cancel: {
                ngClick: "cancelUpdate(project.id, project.name)",
                awToolTip: 'Cancel the SCM update',
                ngShow: "(project.status == 'updating' || project.status == 'running' || project.status == 'pending') && project.summary_fields.user_capabilities.start",
                dataPlacement: 'top'
            }
        }
    });
