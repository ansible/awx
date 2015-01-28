/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Hosts.js
 *  List view object for Hosts data model.
 *
 *
 */



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