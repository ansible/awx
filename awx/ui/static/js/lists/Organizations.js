/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Organizations.js 
 *  List view object for Organizations data model.
 *
 * 
 */
angular.module('OrganizationListDefinition', [])
    .value(
    'OrganizationList', {
        
        name: 'organizations',
        iterator: 'organization',
        selectTitle: 'Add Organizations',
        editTitle: 'Organizations',
        hover: true,
        index: true,
        
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
                mode: 'all',                  // One of: edit, select, all
                ngClick: 'addOrganization()',
                "class": 'btn-success btn-xs',
                awToolTip: 'Create a new organization'
                }
            },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editOrganization(\{\{ organization.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-xs btn-default',
                awToolTip: 'View/Edit organization'
                },

            "delete": {
                label: 'Delete',
                ngClick: "deleteOrganization(\{\{ organization.id \}\},'\{\{ organization.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-xs btn-danger',
                awToolTip: 'Delete organization'
                }
            }
        });
