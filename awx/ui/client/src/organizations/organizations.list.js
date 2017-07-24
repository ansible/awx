/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default [function() {
    return {
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
                columnClass: 'col-lg-4 col-md-6 col-sm-8 col-xs-8',
                awToolTip: '{{organization.description | sanitize}}',
                dataPlacement: 'top'
            },
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addOrganization()',
                awToolTip: 'Create a new organization',
                awFeature: 'multiple_organizations',
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD'
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
    };
}];
