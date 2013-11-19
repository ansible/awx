/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Teams.js 
 *  List view object for Team data model.
 *
 *  
 */
angular.module('TeamsListDefinition', [])
    .value(
    'TeamList', {
        
        name: 'teams',
        iterator: 'team',
        selectTitle: 'Add Team',
        editTitle: 'Teams',
        selectInstructions: 'Click on a row to select it, and click Finished when done. Use the green <i class=\"icon-plus\"></i> button to create a new row.', 
        index: true,
        hover: true, 

        fields: {
            name: {
                key: true,
                label: 'Name'
                },
            description: {
                label: 'Description'
                },
            organization: {
                label: 'Organization',
                ngBind: 'team.organization_name',
                sourceModel: 'organization',
                sourceField: 'name'
                }
            },
        
        actions: {
            add: {
                label: 'Create New',
                icon: 'icon-plus',
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addTeam()',
                "class": 'btn-xs btn-success',
                awToolTip: 'Create a new team'
                },
            stream: {
                'class': "btn-primary btn-xs activity-btn",
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                dataPlacement: "top",
                icon: "icon-comments-alt",
                mode: 'all',
                iconSize: 'large'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editTeam(\{\{ team.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-xs btn-default',
                awToolTip: 'View/Edit team'
                },

            "delete": {
                label: 'Delete',
                ngClick: "deleteTeam(\{\{ team.id \}\},'\{\{ team.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-xs btn-danger',
                awToolTip: 'Delete team'
                }
            }
        });
