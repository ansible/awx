/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Credentials.js 
 *  List view object for Credential data model.
 *
 *  @dict
 */
angular.module('CredentialsListDefinition', [])
    .value(
    'CredentialList', {
        
        name: 'credentials',
        iterator: 'credential',
        selectTitle: 'Add Credentials',
        editTitle: 'Credentials',
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
            kind: {
                label: 'Type',
                searchType: 'select',
                searchOptions: [],   // will be set by Options call to credentials resource
                excludeModal: true,
                nosort: true
                }
            /*
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
            */
            },
        
        actions: {
            add: {
                icon: 'icon-plus',
                label: 'Create New',
                mode: 'all',                         // One of: edit, select, all
                ngClick: 'addCredential()',
                "class": 'btn-success btn-xs',
                awToolTip: 'Create a new credential'
                },
            reset: {
                dataPlacement: 'top',
                icon: "icon-undo",
                mode: 'all',
                'class': 'btn-xs btn-primary',
                awToolTip: "Reset the search filter",
                ngClick: "resetSearch()",
                iconSize: 'large'
                },
            stream: {
                'class': "btn-primary btn-xs activity-btn",
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                dataPlacement: "top",
                icon: "icon-comments-alt",
                mode: 'all',
                iconSize: 'large',
                ngShow: "user_is_superuser"
                }
            },

        fieldActions: {
            edit: {
                ngClick: "editCredential(\{\{ credential.id \}\})",
                icon: 'icon-edit',
                label: 'Edit',
                "class": 'btn-xs btn-default',
                awToolTip: 'View/Edit credential'
                },

            "delete": {
                ngClick: "deleteCredential(\{\{ credential.id \}\},'\{\{ credential.name \}\}')",
                icon: 'icon-trash',
                label: 'Delete',
                "class": 'btn-xs btn-danger',
                awToolTip: 'Delete credential'
                }
            }
        });
