/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 



export default
    angular.module('CloudCredentialsListDefinition', [])
    .value('CloudCredentialList', {

        name: 'cloudcredentials',
        iterator: 'cloudcredential',
        selectTitle: 'Add Cloud Credentials',
        editTitle: 'Cloud Credentials',
        selectInstructions: '<p>Select existing credentials by clicking each credential or checking the related checkbox. When finished, click the blue ' +
            '<em>Select</em> button, located bottom right.</p> <p>Create a brand new credential by clicking the <i class=\"fa fa-plus"></i> button.</p>',
        index: false,
        hover: true,

        fields: {
            name: {
                key: true,
                label: 'Name'
            },
            description: {
                label: 'Description',
                excludeModal: false
            },
            team: {
                label: 'Team',
                ngBind: 'credential.team_name',
                sourceModel: 'team',
                sourceField: 'name',
                excludeModal: true
            },
            user: {
                label: 'User',
                ngBind: 'credential.user_username',
                sourceModel: 'user',
                sourceField: 'username',
                excludeModal: true
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addCredential()',
                "class": 'btn-sm',
                awToolTip: 'Create a new credential'
            }
        },

        fieldActions: {
            edit: {
                ngClick: "editCredential(credential.id)",
                icon: 'fa-edit',
                label: 'Edit',
                "class": 'btn-sm',
                awToolTip: 'Edit credential',
                dataPlacement: 'top'
            },

            "delete": {
                ngClick: "deleteCredential(credential.id, credential.name)",
                icon: 'fa-trash-o',
                label: 'Delete',
                "class": 'btn-sm',
                awToolTip: 'Delete credential',
                dataPlacement: 'top'
            }
        }
    });
