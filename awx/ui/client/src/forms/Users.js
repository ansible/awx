/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

  /**
 * @ngdoc function
 * @name forms.function:Users
 * @description This form is for adding/editing users
*/

export default
    angular.module('UserFormDefinition', [])
        .factory('UserForm', ['i18n', function(i18n) {
        return {

            addTitle: i18n._('New User'),
            editTitle: '{{ username }}',
            name: 'user',
            forceListeners: true,
            tabs: true,

            fields: {
                first_name: {
                    label: i18n._('First Name'),
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: true,
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                last_name: {
                    label: i18n._('Last Name'),
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: true,
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                email: {
                    label: i18n._('Email'),
                    type: 'email',
                    addRequired: true,
                    editRequired: true,
                    autocomplete: false,
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                username: {
                    label: i18n._('Username'),
                    type: 'text',
                    awRequiredWhen: {
                        reqExpression: "not_ldap_user && external_account === null",
                        init: true
                    },
                    autocomplete: false,
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                organization: {
                    label: i18n._('Organization'),
                    type: 'lookup',
                    sourceModel: 'organization',
                    sourceField: 'name',
                    addRequired: true,
                    editRequired: false,
                    excludeMode: 'edit',
                    ngClick: 'lookUpOrganization()',
                    awRequiredWhen: {
                        reqExpression: "orgrequired",
                        init: true
                    },
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                password: {
                    label: i18n._('Password'),
                    type: 'sensitive',
                    hasShowInputButton: true,
                    ngShow: 'ldap_user == false && socialAuthUser === false && external_account === null',
                    addRequired: true,
                    editRequired: false,
                    ngChange: "clearPWConfirm('password_confirm')",
                    autocomplete: false,
                    chkPass: true,
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                password_confirm: {
                    label: i18n._('Confirm Password'),
                    type: 'sensitive',
                    hasShowInputButton: true,
                    ngShow: 'ldap_user == false && socialAuthUser === false && external_account === null',
                    addRequired: true,
                    editRequired: false,
                    awPassMatch: true,
                    associated: 'password',
                    autocomplete: false,
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                user_type: {
                    label: i18n._('User Type'),
                    type: 'select',
                    ngOptions: 'item as item.label for item in user_type_options track by item.type',
                    disableChooseOption: true,
                    ngModel: 'user_type',
                    ngShow: 'current_user["is_superuser"]',
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
            },

            buttons: {
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: '(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                save: {
                    ngClick: 'formSave()',
                    ngDisabled: true,
                    ngShow: '(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                }
            },

            related: {
                organizations: {
                    basePath: 'users/:id/organizations',
                    awToolTip: i18n._('Please save before assigning to organizations'),
                    dataPlacement: 'top',
                    type: 'collection',
                    title: i18n._('Organizations'),
                    iterator: 'organization',
                    index: false,
                    open: false,

                    actions: {},

                    fields: {
                        name: {
                            key: true,
                            label: 'Name'
                        },
                        description: {
                            label: 'Description'
                        }
                    },
                    hideOnSuperuser: true
                },
                teams: {
                    basePath: 'users/:id/teams',
                    awToolTip: i18n._('Please save before assigning to teams'),
                    dataPlacement: 'top',
                    type: 'collection',
                    title: i18n._('Teams'),
                    iterator: 'team',
                    open: false,
                    index: false,
                    actions: {},

                    fields: {
                        name: {
                            key: true,
                            label: 'Name'
                        },
                        description: {
                            label: 'Description'
                        }
                    },
                    hideOnSuperuser: true
                },
                roles: {
                    awToolTip: i18n._('Please save before assigning to organizations'),
                    dataPlacement: 'top',
                    hideSearchAndActions: true,
                    type: 'collection',
                    title: i18n._('Granted permissions'),
                    iterator: 'permission',
                    open: false,
                    index: false,
                    emptyListText: i18n._('No permissions have been granted'),
                    fields: {
                        name: {
                            label: i18n._('Name'),
                            ngBind: 'permission.summary_fields.resource_name',
                            linkTo: '{{convertApiUrl(permission.related[permission.summary_fields.resource_type])}}',
                            noSort: true
                        },
                        type: {
                            label: i18n._('Type'),
                            ngBind: 'permission.summary_fields.resource_type_display_name',
                            noSort: true
                        },
                        role: {
                            label: i18n._('Role'),
                            ngBind: 'permission.name',
                            noSort: true
                        },
                    },
                    fieldActions: {
                        "delete": {
                            label: i18n._('Remove'),
                            ngClick: 'deletePermissionFromUser(user_id, username, permission.name, permission.summary_fields.resource_name, permission.related.users)',
                            iconClass: 'fa fa-times',
                            awToolTip: i18n._('Dissasociate permission from user'),
                            ngShow: 'permission.summary_fields.user_capabilities.unattach'
                        }
                    },
                    hideOnSuperuser: true
                }
            }

        };}]);
