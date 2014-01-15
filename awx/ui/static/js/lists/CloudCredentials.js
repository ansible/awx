/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  CloudCredentials.js 
 *  List view object for Credential data model.
 *
 *  @dict
 */
angular.module('CloudCredentialsListDefinition', [])
    .value(
    'CloudCredentialList', {
        
        name: 'cloudcredentials',
        iterator: 'cloudcredential',
        selectTitle: 'Add Cloud Credentials',
        editTitle: 'Cloud Credentials',
        selectInstructions: '<p>Select existing credentials by clicking each credential or checking the related checkbox. When finished, click the blue ' +
            '<em>Select</em> button, located bottom right.</p> <p>Create a brand new credential by clicking the green <em>Create New</em> button.</p>',
        index: true,
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
                mode: 'all',                         // One of: edit, select, all
                ngClick: 'addCredential()',
                "class": 'btn-sm',
                awToolTip: 'Create a new credential'
                }
            },

        fieldActions: {
            edit: {
                ngClick: "editCredential(\{\{ credential.id \}\})",
                icon: 'fa-edit',
                label: 'Edit',
                "class": 'btn-sm',
                awToolTip: 'Edit credential',
                dataPlacement: 'top'
                },

            "delete": {
                ngClick: "deleteCredential(\{\{ credential.id \}\},'\{\{ credential.name \}\}')",
                icon: 'fa-trash-o',
                label: 'Delete',
                "class": 'btn-sm',
                awToolTip: 'Delete credential',
                dataPlacement: 'top'
                }
            }
        });
