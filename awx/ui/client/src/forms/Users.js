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
        .value('UserForm', {

            addTitle: 'New User',
            editTitle: '{{ username }}',
            name: 'user',
            forceListeners: true,
            tabs: true,

            fields: {
                first_name: {
                    label: 'First Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: true,
                    ngDisabled: '!user_obj.summary_fields.user_capabilities.edit'
                },
                last_name: {
                    label: 'Last Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: true,
                    ngDisabled: '!user_obj.summary_fields.user_capabilities.edit'
                },
                email: {
                    label: 'Email',
                    type: 'email',
                    addRequired: true,
                    editRequired: true,
                    autocomplete: false,
                    ngDisabled: '!user_obj.summary_fields.user_capabilities.edit'
                },
                username: {
                    label: 'Username',
                    type: 'text',
                    awRequiredWhen: {
                        reqExpression: "not_ldap_user && external_account === null",
                        init: true
                    },
                    autocomplete: false,
                    ngDisabled: '!user_obj.summary_fields.user_capabilities.edit'
                },
                organization: {
                    label: 'Organization',
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
                    ngDisabled: '!user_obj.summary_fields.user_capabilities.edit'
                },
                password: {
                    label: 'Password',
                    type: 'sensitive',
                    hasShowInputButton: true,
                    ngShow: 'ldap_user == false && socialAuthUser === false && external_account === null',
                    addRequired: true,
                    editRequired: false,
                    ngChange: "clearPWConfirm('password_confirm')",
                    autocomplete: false,
                    chkPass: true,
                    ngDisabled: '!user_obj.summary_fields.user_capabilities.edit'
                },
                password_confirm: {
                    label: 'Confirm Password',
                    type: 'sensitive',
                    hasShowInputButton: true,
                    ngShow: 'ldap_user == false && socialAuthUser === false && external_account === null',
                    addRequired: true,
                    editRequired: false,
                    awPassMatch: true,
                    associated: 'password',
                    autocomplete: false,
                    ngDisabled: '!user_obj.summary_fields.user_capabilities.edit'
                },
                user_type: {
                    label: 'User Type',
                    type: 'select',
                    ngOptions: 'item as item.label for item in user_type_options track by item.type',
                    disableChooseOption: true,
                    ngModel: 'user_type',
                    ngShow: 'current_user["is_superuser"]',
                    ngDisabled: '!user_obj.summary_fields.user_capabilities.edit'
                },
            },

            buttons: {
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: 'user_obj.summary_fields.user_capabilities.edit'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!user_obj.summary_fields.user_capabilities.edit'
                },
                save: {
                    ngClick: 'formSave()',
                    ngDisabled: true,
                    ngShow: 'user_obj.summary_fields.user_capabilities.edit'
                }
            },

            related: {
                organizations: {
                    basePath: 'users/:id/organizations',
                    awToolTip: 'Please save before assigning to organizations',
                    dataPlacement: 'top',
                    type: 'collection',
                    title: 'Organizations',
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
                    awToolTip: 'Please save before assigning to teams',
                    dataPlacement: 'top',
                    type: 'collection',
                    title: 'Teams',
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
                    awToolTip: 'Please save before assigning to organizations',
                    dataPlacement: 'top',
                    hideSearchAndActions: true,
                    type: 'collection',
                    title: 'Granted permissions',
                    iterator: 'permission',
                    open: false,
                    index: false,
                    emptyListText: 'No permissions have been granted',
                    fields: {
                        name: {
                            label: 'Name',
                            ngBind: 'permission.summary_fields.resource_name',
                            linkTo: '{{convertApiUrl(permission.related[permission.summary_fields.resource_type])}}',
                            noSort: true
                        },
                        type: {
                            label: 'Type',
                            ngBind: 'permission.summary_fields.resource_type_display_name',
                            noSort: true
                        },
                        role: {
                            label: 'Role',
                            ngBind: 'permission.name',
                            noSort: true
                        },
                    },
                    fieldActions: {
                        "delete": {
                            label: 'Remove',
                            ngClick: 'deletePermissionFromUser(user_id, username, permission.name, permission.summary_fields.resource_name, permission.related.users)',
                            iconClass: 'fa fa-times',
                            awToolTip: 'Dissasociate permission from user',
                            ngShow: 'permission.summary_fields.user_capabilities.unattach'
                        }
                    },
                    hideOnSuperuser: true
                }
            }

        });
