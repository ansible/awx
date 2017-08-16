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
                columnClass: 'col-md-3 col-sm-9 col-xs-9',
                modalColumnClass: 'col-md-11',
                awToolTip: '{{credential_type.description | sanitize}}',
                dataPlacement: 'top'
            },
            kind: {
                label: i18n._('Kind'),
                ngBind: 'credential_type.kind_label',
                excludeModal: true,
                columnClass: 'col-md-2 hidden-sm hidden-xs'
            },
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addCredentialType()',
                awToolTip: i18n._('Create a new credential type'),
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ' + i18n._('ADD'),
                ngShow: 'canAdd'
            }
        },

        fieldActions: {

            columnClass: 'col-md-2 col-sm-3 col-xs-3',

            edit: {
                ngClick: "editCredentialType(credential_type.id)",
                icon: 'fa-edit',
                label: i18n._('Edit'),
                "class": 'btn-sm',
                awToolTip: i18n._('Edit credenital type'),
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
