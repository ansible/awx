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
        editTitle: '{{ name }}',
        selectInstructions: '<p>Select existing projects by clicking each project or checking the related checkbox. When finished, click the blue ' +
            '<em>Select</em> button, located bottom right.</p> <p>Create a brand new project by clicking the green <em>Create New</em> button.</p>', 
        index: true,
        hover: true, 
        
        fields: {
            name: {
                key: true,
                label: 'Name'
                },
            description: {
                label: 'Description'
                }
            },
        
        actions: {
            add: {
                label: 'Create New',
                icon: 'icon-plus',
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addProject()',
                "class": 'btn-success btn-mini',
                awToolTip: 'Create a new project'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editProject(\{\{ project.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-mini',
                awToolTip: 'View/edit project'
                },

            "delete": {
                label: 'Delete',
                ngClick: "deleteProject(\{\{ project.id \}\},'\{\{ project.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-mini btn-danger',
                awToolTip: 'Delete project'
                }
            }
        });
