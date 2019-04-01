/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
    return {
        // editTitle: 'Authorization Configuration',
        name: 'configuration_ldap2_template',
        showActions: true,
        showHeader: false,

        fields: {
            AUTH_LDAP_2_SERVER_URI: {
                type: 'text',
                reset: 'AUTH_LDAP_2_SERVER_URI'
            },
            AUTH_LDAP_2_BIND_DN: {
                type: 'text',
                reset: 'AUTH_LDAP_2_BIND_DN'
            },
            AUTH_LDAP_2_BIND_PASSWORD: {
                type: 'sensitive',
                hasShowInputButton: true,
            },
            AUTH_LDAP_2_USER_SEARCH: {
                type: 'textarea',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                reset: 'AUTH_LDAP_2_USER_SEARCH'
            },
            AUTH_LDAP_2_GROUP_SEARCH: {
                type: 'textarea',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                reset: 'AUTH_LDAP_2_GROUP_SEARCH'
            },
            AUTH_LDAP_2_USER_DN_TEMPLATE: {
                type: 'text',
                reset: 'AUTH_LDAP_2_USER_DN_TEMPLATE'
            },
            AUTH_LDAP_2_USER_ATTR_MAP: {
                type: 'textarea',
                reset: 'AUTH_LDAP_2_USER_ATTR_MAP',
                rows: 6,
                codeMirror: true,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
            },
            AUTH_LDAP_2_GROUP_TYPE: {
                type: 'select',
                reset: 'AUTH_LDAP_2_GROUP_TYPE',
                ngOptions: 'group.label for group in AUTH_LDAP_2_GROUP_TYPE_options track by group.value',
            },
            AUTH_LDAP_2_GROUP_TYPE_PARAMS: {
                type: 'textarea',
                reset: 'AUTH_LDAP_2_GROUP_TYPE_PARAMS',
                codeMirror: true,
                rows: 6,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
            },
            AUTH_LDAP_2_REQUIRE_GROUP: {
                type: 'text',
                reset: 'AUTH_LDAP_2_REQUIRE_GROUP'
            },
            AUTH_LDAP_2_DENY_GROUP: {
                type: 'text',
                reset: 'AUTH_LDAP_2_DENY_GROUP'
            },
            AUTH_LDAP_2_START_TLS: {
                type: 'toggleSwitch'
            },
            AUTH_LDAP_2_USER_FLAGS_BY_GROUP: {
                type: 'textarea',
                reset: 'AUTH_LDAP_2_USER_FLAGS_BY_GROUP',
                codeMirror: true,
                rows: 6,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
            },
            AUTH_LDAP_2_ORGANIZATION_MAP: {
                type: 'textarea',
                reset: 'AUTH_LDAP_2_ORGANIZATION_MAP',
                codeMirror: true,
                rows: 6,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
            },
            AUTH_LDAP_2_TEAM_MAP: {
                type: 'textarea',
                reset: 'AUTH_LDAP_2_TEAM_MAP',
                codeMirror: true,
                rows: 6,
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
            }
        },

        buttons: {
            reset: {
                ngShow: '!user_is_system_auditor',
                ngClick: 'vm.resetAllConfirm()',
                label: i18n._('Revert all to default'),
                class: 'Form-resetAll'
            },
            cancel: {
                ngClick: 'vm.formCancel()',
            },
            save: {
                ngClick: 'vm.formSave()',
                ngDisabled: "configuration_ldap2_template_form.$invalid || configuration_ldap2_template_form.$pending"
            }
        }
    };
}
];
