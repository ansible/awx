/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Credentials.js
 *  List view object for Credential data model.
 *
 *  @dict
 */



export default
    angular.module('CustomInventoryListDefinition', [])
    .value('CustomInventoryList', {

        name:  'source_scripts' ,  // 'custom_inventories',
        iterator: 'source_script',  //'custom_inventory',
        selectTitle: 'Add custom inventory',
        editTitle: 'Custom Inventories',
        index: false,
        hover: false,

        fields: {
            name: {
                key: true,
                noLink: true,
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
                ngBind: 'source_script.summary_fields.organization.name',
                // linkTo: '/#/organizations/{{ custom_inventory.organization }}',
                sourceModel: 'organization',
                sourceField: 'name',
                excludeModal: true,
                columnClass: 'col-md-4 hidden-sm hidden-xs'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addCustomInv()',
                awToolTip: 'Create a new credential'
            },
        },

        fieldActions: {
            edit: {
                ngClick: "editCustomInv(source_script.id)",
                icon: 'fa-edit',
                label: 'Edit',
                "class": 'btn-sm',
                awToolTip: 'Edit credential',
                dataPlacement: 'top'
            },

            "delete": {
                ngClick: "deleteCustomInv(source_script.id, source_script.name)",
                icon: 'fa-trash',
                label: 'Delete',
                "class": 'btn-sm',
                awToolTip: 'Delete credential',
                dataPlacement: 'top'
            }
        }
    });
