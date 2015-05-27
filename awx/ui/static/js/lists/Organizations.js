/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 

export default
    angular.module('OrganizationListDefinition', [])
    .value('OrganizationList', {

        name: 'organizations',
        iterator: 'organization',
        selectTitle: 'Add Organizations',
        selectInstructions: '<p>Select existing organizations by clicking each organization or checking the related checkbox. When finished, ' +
            'click the blue <em>Select</em> button, located bottom right.</p><p>Create a new organization by clicking the ' +
            '<i class=\"fa fa-plus\"></i> button.</p>',
        editTitle: 'Organizations',
        hover: true,
        index: false,

        fields: {
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-lg-4 col-md-6 col-sm-8 col-xs-8'
            },
            description: {
                label: 'Description',
                columnClass: 'hidden-sm hidden-xs',
                excludeModal: true
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addOrganization()',
                awToolTip: 'Create a new organization',
                awFeature: 'multiple_organizations'
            },
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                mode: 'edit',
                awFeature: 'activity_streams'
            }
        },

        fieldActions: {
            edit: {
                label: 'Edit',
                ngClick: "editOrganization(organization.id)",
                icon: 'icon-edit',
                "class": 'btn-xs btn-default',
                awToolTip: 'Edit organization',
                dataPlacement: 'top'
            },

            "delete": {
                label: 'Delete',
                ngClick: "deleteOrganization(organization.id, organization.name)",
                icon: 'icon-trash',
                "class": 'btn-xs btn-danger',
                awToolTip: 'Delete organization',
                dataPlacement: 'top'
            }
        }
    });
