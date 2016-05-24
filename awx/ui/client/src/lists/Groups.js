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
        fields: {
            name: {
                key: true,
                label: 'Target Group Name'
            }
        }
    });
