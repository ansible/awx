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
                label: 'Descriptions'
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
                label: 'Add',
                icon: 'icon-plus',
                mode: 'all',             // One of: edit, select, all
                ngClick: 'addTeam()',
                class: 'btn-success btn-small',
                awToolTip: 'Create a new team'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editTeam(\{\{ team.id \}\})",
                icon: 'icon-edit',
                class: 'btn-small btn-success',
                awToolTip: 'View/Edit team'
                },

            delete: {
                label: 'Delete',
                ngClick: "deleteTeam(\{\{ team.id \}\},'\{\{ team.name \}\}')",
                icon: 'icon-remove',
                class: 'btn-small btn-danger',
                awToolTip: 'Delete team'
                }
            }
        });
