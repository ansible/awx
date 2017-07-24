/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/



export default ['i18n', function(i18n){
    return {
        name:  'inventory_scripts' ,
        listTitle: i18n._('INVENTORY SCRIPTS'),
        iterator: 'inventory_script',
        index: false,
        hover: false,

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-3 col-sm-9 col-xs-9',
                modalColumnClass: 'col-md-8',
                awToolTip: '{{inventory_script.description | sanitize}}',
                dataPlacement: 'top'
            },
            organization: {
                label: i18n._('Organization'),
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
                awToolTip: i18n._('Create a new custom inventory'),
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ' + i18n._('ADD'),
                ngShow: 'canAdd'
            }
        },

        fieldActions: {

            columnClass: 'col-md-2 col-sm-3 col-xs-3',

            edit: {
                ngClick: "editCustomInv(inventory_script.id)",
                icon: 'fa-edit',
                label: i18n._('Edit'),
                "class": 'btn-sm',
                awToolTip: i18n._('Edit inventory script'),
                dataPlacement: 'top',
                ngShow: 'inventory_script.summary_fields.user_capabilities.edit'
            },
            view: {
                ngClick: "editCustomInv(inventory_script.id)",
                label: i18n._('View'),
                "class": 'btn-sm',
                awToolTip: i18n._('View inventory script'),
                dataPlacement: 'top',
                ngShow: '!inventory_script.summary_fields.user_capabilities.edit'
            },
            "delete": {
                ngClick: "deleteCustomInv(inventory_script.id, inventory_script.name)",
                icon: 'fa-trash',
                label: i18n._('Delete'),
                "class": 'btn-sm',
                awToolTip: i18n._('Delete inventory script'),
                dataPlacement: 'top',
                ngShow: 'inventory_script.summary_fields.user_capabilities.delete'
            }
        }
    };
}];
