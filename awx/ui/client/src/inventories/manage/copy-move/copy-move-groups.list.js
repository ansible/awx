/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/




export default {
    name: 'groups',
    iterator: 'copy',
    selectTitle: 'Copy Groups',
    index: false,
    well: false,
    emptyListText: 'PLEASE CREATE ADDITIONAL GROUPS / HOSTS TO PERFORM THIS ACTION',
    fields: {
        name: {
            key: true,
            label: 'Target Group Name'
        }
    },
    basePath: 'api/v1/inventories/{{$stateParams.inventory_id}}/groups'
};
