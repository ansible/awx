/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    angular.module('AdminListDefinition', [])
    .value('AdminList', {

        name: 'admins',
        iterator: 'admin',
        selectTitle: 'Add Administrators',
        editTitle: 'Admins',
        selectInstructions: '<p>Select existing users by clicking each user or checking the related checkbox. When finished, click the blue ' +
            '<em>Select</em> button, located bottom right.</p>',
        base: 'users',
        index: false,
        hover: true,

        fields: {
            username: {
                key: true,
                label: 'Username'
            },
            first_name: {
                label: 'First Name'
            },
            last_name: {
                label: 'Last Name'
            }
        },

        actions: {},

        fieldActions: {}
    });
