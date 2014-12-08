/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Credentials.js
 *  List view object for Credential data model.
 *
 *  @dict
 */

'use strict';

angular.module('CustomInventoryListDefinition', [])
    .value('CustomInventoryList', {

        name: 'custom_inventories',
        iterator: 'custom_inventory',
        selectTitle: 'Add custom inventory',
        editTitle: 'Custom Inventories',
        selectInstructions: "<p>Select existing credentials by clicking each credential or checking the related checkbox. When " +
            "finished, click the blue <em>Select</em> button, located bottom right.</p> <p>Create a brand new credential by clicking " +
            "the <i class=\"fa fa-plus\"></i> button.</p><div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>",
        index: false,
        hover: true,

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
                ngBind: 'custom_inventory.summary_fields.organization.name',
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
                ngClick: "editCustomInv(custom_inventory.id)",
                icon: 'fa-edit',
                label: 'Edit',
                "class": 'btn-sm',
                awToolTip: 'Edit credential',
                dataPlacement: 'top'
            },

            "delete": {
                ngClick: "deleteCustomInv(custom_inventory.id, custom_inventory.name)",
                icon: 'fa-trash',
                label: 'Delete',
                "class": 'btn-sm',
                awToolTip: 'Delete credential',
                dataPlacement: 'top'
            }
        }
    });
