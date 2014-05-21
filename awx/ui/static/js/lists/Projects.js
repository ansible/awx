/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Projects.js
 *  List view object for Project data model.
 *
 *
 */

'use strict';

angular.module('ProjectsListDefinition', [])
    .value('ProjectList', {

        name: 'projects',
        iterator: 'project',
        selectTitle: 'Add Project',
        editTitle: 'Projects',
        selectInstructions: '<p>Select existing projects by clicking each project or checking the related checkbox. When finished, click the blue ' +
            '<em>Select</em> button, located bottom right.</p> <p>Create a brand new project by clicking the green <em>Create New</em> button.</p>',
        index: true,
        hover: true,

        fields: {
            status: {
                label: 'Status',
                iconOnly: true,
                ngClick: 'showSCMStatus(project.id)',
                awToolTip: '{{ project.statusTip }}',
                dataTipWatch: 'project.statusTip',
                dataPlacement: 'top',
                icon: "icon-job-{{ project.statusIcon }}",
                columnClass: "col-lg-1 col-md-1 col-sm-2 col-xs-2",
                nosort: true,
                searchType: 'select',
                searchOptions: [],  //set in the controller
                excludeModal: true
            },
            name: {
                key: true,
                label: 'Name',
                columnClass: "col-lg-6 col-md-4 col-sm-6 col-xs-6",
                modalColumnClass: 'col-md-8'
            },
            last_updated: {
                label: 'Last Updated',
                filter: "date:'MM/dd/yy HH:mm:ss'",
                columnClass: "col-lg-2 col-md-2 hidden-sm hidden-xs",
                excludeModal: true,
                searchable: false,
                nosort: true
            },
            scm_type: {
                label: 'Type',
                searchType: 'select',
                searchOptions: [], // will be set by Options call to projects resource
                excludeModal: true,
                columnClass: 'col-md-2 hidden-sm hidden-xs'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addProject()',
                awToolTip: 'Create a new project'
            },
            /*help: {
                awPopOver: "<dl>\n<dt>Updating</dt><dd>A source control update is in progress.</dd>\n" +
                    "<dt>Never Updated</dt><dd>This project has not yet been updated from source control.</dd>\n" +
                    "<dt>Failed</dt><dd>An error occurred during the most recent source control update, click the status " +
                    "text for more information.</dd>\n" +
                    "<dt>Successful</dt><dd>TThe latest source control update completed successfully.</dd>\n" +
                    "<dt>Missing</dt><dd>The previously configured local project directory is missing.</dd>\n" +
                    "<dt>N/A</dt><dd>The project is not linked to source control, so updates are not applicable.</dd>\n" +
                    "</dl>\n",
                dataPlacement: 'left',
                dataContainer: 'body',
                mode: 'edit',
                awToolTip: 'Click for help',
                awTipPlacement: 'top'
            },*/
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refresh()",
                ngShow: "socketStatus == 'error'"
            },
            /*socket: {
                mode: 'all',
                iconClass: "{{ 'fa fa-power-off fa-lg socket-' + socketStatus }}",
                awToolTip: "{{ socketTip }}",
                dataTipWatch: "socketTip",
                ngClick: "socketToggle()",
            },*/
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                mode: 'edit'
            }
        },

        fieldActions: {
            scm_update: {
                ngClick: 'SCMUpdate(project.id, $event)',
                awToolTip: "{{ project.scm_update_tooltip }}",
                dataTipWatch: "project.scm_update_tooltip",
                ngClass: "project.scm_type_class",
                dataPlacement: 'top'
            },
            schedule: {
                mode: 'all',
                ngClick: "editSchedules(project.id)",
                awToolTip: "{{ project.scm_schedule_tooltip }}",
                ngClass: "project.scm_type_class",
                dataPlacement: 'top'
            },
            edit: {
                ngClick: "editProject(project.id)",
                awToolTip: 'Edit the project',
                dataPlacement: 'top'
            },
            "delete": {
                ngClick: "deleteProject(project.id, project.name)",
                awToolTip: 'Delete the project',
                ngShow: "project.status !== 'updating' && project.status !== 'running' && project.status !== 'pending'",
                dataPlacement: 'top'
            },
            cancel: {
                ngClick: "cancelUpdate(project.id, project.name)",
                awToolTip: 'Cancel the SCM update',
                ngShow: "project.status == 'updating' || project.status == 'running' || project.status == 'pending'",
                dataPlacement: 'top'
            }
        }
    });