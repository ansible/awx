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
        selectInstructions: 'Check the Select checkbox next to each project to be added, and click Finished when done. Use the green <i class=\"icon-plus\"></i> button to create a new project.', 
        
        fields: {
            name: {
                key: true,
                label: 'Name'
                },
            description: {
                label: 'Descriptions'
                }
            },
        
        actions: {
            add: {
                icon: 'icon-plus',
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addProject()',
                class: 'btn btn-success',
                awToolTip: 'Create a new project'
                }
            },

        fieldActions: {
            edit: {
                ngClick: "editProject(\{\{ project.id \}\})",
                icon: 'icon-edit',
                awToolTip: 'Edit project'
                },

            delete: {
                ngClick: "deleteProject(\{\{ project.id \}\},'\{\{ project.name \}\}')",
                icon: 'icon-remove',
                class: 'btn-danger',
                awToolTip: 'Delete project'
                }
            }
        });
