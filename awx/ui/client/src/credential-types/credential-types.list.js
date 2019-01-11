/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/



export default ['i18n', function(i18n){
    return {
        name:  'credential_types' ,
        listTitle: i18n._('CREDENTIAL TYPES'),
        basePath: 'credential_types',
        iterator: 'credential_type',
        index: false,
        hover: false,
        search: {
            managed_by_tower: 'false'
        },

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-4 col-sm-9 col-xs-9',
                modalColumnClass: 'col-sm-12',
                awToolTip: '{{credential_type.description | sanitize}}',
                dataPlacement: 'top'
            },
            kind: {
                label: i18n._('Kind'),
                ngBind: 'credential_type.kind_label',
                excludeModal: true,
                columnClass: 'd-none d-md-flex col-md-4'
            },
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addCredentialType()',
                awToolTip: i18n._('Create a new credential type'),
                actionClass: 'at-Button--add',
                actionId: 'button-add',
                ngShow: 'canAdd'
            }
        },

        fieldActions: {

            columnClass: 'col-md-4 col-sm-3 col-xs-3',

            edit: {
                ngClick: "editCredentialType(credential_type.id)",
                icon: 'fa-edit',
                label: i18n._('Edit'),
                "class": 'btn-sm',
                awToolTip: i18n._('Edit credential type'),
                dataPlacement: 'top',
                ngShow: 'credential_type.summary_fields.user_capabilities.edit'
            },
            view: {
                ngClick: "editCredentialType(credential_type.id)",
                label: i18n._('View'),
                "class": 'btn-sm',
                awToolTip: i18n._('View credential type'),
                dataPlacement: 'top',
                ngShow: '!credential_type.summary_fields.user_capabilities.edit'
            },
            "delete": {
                ngClick: "deleteCredentialType(credential_type.id, credential_type.name)",
                icon: 'fa-trash',
                label: i18n._('Delete'),
                "class": 'btn-sm',
                awToolTip: i18n._('Delete credential type'),
                dataPlacement: 'top',
                ngShow: 'credential_type.summary_fields.user_capabilities.delete'
            }
        }
    };
}];
