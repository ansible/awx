/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/



export default function(){
    return {
        name:  'inventory_scripts' ,
        iterator: 'inventory_script',
        index: false,
        hover: false,

        fields: {
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-md-3 col-sm-9 col-xs-9',
                modalColumnClass: 'col-md-8'
            },
            description: {
                label: 'Description',
                excludeModal: true,
                columnClass: 'col-md-4 hidden-sm hidden-xs'
            },
            organization: {
                label: 'Organization',
                ngBind: 'inventory_script.summary_fields.organization.name',
                sourceModel: 'organization',
                sourceField: 'name',
                excludeModal: true,
                columnClass: 'col-md-3 hidden-sm hidden-xs'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addCustomInv()',
                awToolTip: 'Create a new credential'
            },
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                icon: "icon-comments-alt",
                mode: 'edit',
                awFeature: 'activity_streams'
            }
        },

        fieldActions: {
            edit: {
                ngClick: "editCustomInv(inventory_script.id)",
                icon: 'fa-edit',
                label: 'Edit',
                "class": 'btn-sm',
                awToolTip: 'Edit credential',
                dataPlacement: 'top'
            },
            "delete": {
                ngClick: "deleteCustomInv(inventory_script.id, inventory_script.name)",
                icon: 'fa-trash',
                label: 'Delete',
                "class": 'btn-sm',
                awToolTip: 'Delete credential',
                dataPlacement: 'top'
            }
        }
    };
}
