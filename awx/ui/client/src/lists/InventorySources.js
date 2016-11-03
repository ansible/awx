/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('InventorySourcesListDefinition', [])
    .value('InventorySourcesList', {

        name: 'workflow_inventory_sources',
        iterator: 'inventory_source',
        listTitle: 'Inventory Sources',
        index: false,
        hover: true,

        fields: {
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-md-11'
            }
        },

        actions: {},

        fieldActions: {}
    });
