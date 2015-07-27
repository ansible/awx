/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
export default
    angular.module('HostListDefinition', [])
    .value('HostList', {

        name: 'copy_hosts',
        iterator: 'copy_host',
        selectTitle: 'Add Existing Hosts',
        editTitle: 'Hosts',
        index: false,
        well: false,

        fields: {
            name: {
                key: true,
                label: 'Host Name'
            }
        },

        actions: { },

        fieldActions: { }
    });
