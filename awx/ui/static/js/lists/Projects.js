/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Projects.js 
 *  List view object for Project data model.
 *
 *
 */
angular.module('ProjectsListDefinition', [])
    .value(
    'ProjectList', {
        
        name: 'projects',
        iterator: 'project',
        selectTitle: 'Add Project',
        editTitle: 'Projects',
        selectInstructions: '<p>Select existing projects by clicking each project or checking the related checkbox. When finished, click the blue ' +
            '<em>Select</em> button, located bottom right.</p> <p>Create a brand new project by clicking the green <em>Create New</em> button.</p>', 
        index: true,
        hover: true, 
        
        fields: {
            name: {
                key: true,
                label: 'Name',
                },
            description: {
                label: 'Description',
                columnClass: 'hidden-sm hidden-xs',
                excludeModal: true
                },
            status: {
                label: 'Update Status',
                ngClick: 'showSCMStatus(\{\{ project.id \}\})',
                awToolTip: 'View details of last SCM Update',
                dataPlacement: 'bottom',
                badgeIcon: "\{\{ 'icon-failures-' + project.badge \}\}",
                badgePlacement: 'left'
                },
            last_updated: {
                label: 'Last Updated',
                type: 'date'
                }
            },
        
        actions: {
            add: {
                label: 'Create New',
                icon: 'icon-plus',
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addProject()',
                "class": 'btn-success btn-sm',
                awToolTip: 'Create a new project'
                },
            refresh: {
                label: 'Refresh',
                "class": 'btn-primary btn-sm',
                ngClick: "refresh(\{\{ job.id \}\})",
                icon: 'icon-refresh',
                awToolTip: 'Refresh the page',
                mode: 'all'
                },
            help: {
                awPopOver: "<dl>\n<dt>Updating</dt><dd>An SCM update is in progress.</dd>\n" +
                    "<dt>Never Updated</dt><dd>No SCM update has ever run for the project.</dd>\n" +
                    "<dt>Failed</dt><dd>An error occurred during the most recent SCM update.</dd>\n" +
                    "<dt>Successful</dt><dd>The latest SCM update ran to completion without incident.</dd>\n" +
                    "<dt>Missing</dt><dd>The local project directory is missing.</dd>\n" +
                    "<dt>N/A</dt><dd>The project does not use SCM, so an update status is not available.</dd>\n" +
                    "</dl>\n",
                dataPlacement: 'left',
                dataContainer: 'body',
                icon: "icon-question-sign",
                mode: 'all',
                'class': 'btn-xs btn-info btn-help pull-right',
                awToolTip: 'Click for help',
                dataTitle: 'Project Status',
                iconSize: 'large',
                id: 'project-help-button'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editProject(\{\{ project.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-xs btn-default',
                awToolTip: 'View/edit project properties'
                },
            scm_update: {
                label: 'Update',
                icon: 'icon-cloud-download',
                "class": 'btn-xs btn-success',
                ngClick: 'SCMUpdate(\{\{ project.id \}\})',
                awToolTip: 'Perform an SCM update on this project'     
                },
            "delete": {
                label: 'Delete',
                ngClick: "deleteProject(\{\{ project.id \}\},'\{\{ project.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-xs btn-danger',
                awToolTip: 'Permanently remove project from the database'
                }
            }
        });
