/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/




export default
    angular.module('GroupListDefinition', [])
    .value('CopyMoveGroupList', {

        name: 'groups',
        iterator: 'group',
        selectTitle: 'Copy Groups',
        index: false,
        well: false,
        emptyListText: 'PLEASE CREATE ADDITIONAL GROUPS / HOSTS TO PERFORM THIS ACTION',
        fields: {
            name: {
                key: true,
                label: 'Target Group Name'
            }
        }
    });
