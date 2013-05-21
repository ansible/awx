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
                icon: 'icon-plus',
                mode: 'all',                  // One of: edit, select, all
                ngClick: 'addOrganization()',
                class: 'btn-success',
                awToolTip: 'Create a new row'
                }
            },

        fieldActions: {
            edit: {
                ngClick: "editOrganization(\{\{ organization.id \}\})",
                icon: 'icon-edit',
                class: 'btn-mini',
                awToolTip: 'View/Edit organization'
                },

            delete: {
                ngClick: "deleteOrganization(\{\{ organization.id \}\},'\{\{ organization.name \}\}')",
                icon: 'icon-remove',
                class: 'btn-mini btn-danger',
                awToolTip: 'Delete organization'
                }
            }
        });
