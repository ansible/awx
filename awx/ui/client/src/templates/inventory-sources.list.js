/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default {
    name: 'workflow_inventory_sources',
    iterator: 'inventory_source',
    basePath: 'inventory_sources',
    listTitle: 'INVENTORY SOURCES',
    index: false,
    hover: true,

    fields: {
        name: {
            label: 'Name',
            ngBind: 'inventory_source.summary_fields.group.name',
            columnClass: 'col-md-11',
            simpleTip: {
                awToolTip: "Inventory: {{inventory_source.summary_fields.inventory.name}}",
                dataPlacement: "top"
            }
        }
    },

    actions: {},

    fieldActions: {}
};
