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
                    capitalize: true
                },
                last_name: {
                    label: 'Last Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: true
                },
                email: {
                    label: 'Email',
                    type: 'email',
                    addRequired: true,
                    editRequired: true,
                    autocomplete: false
                },
                username: {
                    label: 'Username',
                    type: 'text',
                    awRequiredWhen: {
                        reqExpression: "not_ldap_user",
                        init: true
                    },
                    autocomplete: false
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
                    }
                },
                password: {
                    label: 'Password',
                    type: 'sensitive',
                    hasShowInputButton: true,
                    ngShow: 'ldap_user == false && socialAuthUser === false',
                    addRequired: true,
                    editRequired: false,
                    ngChange: "clearPWConfirm('password_confirm')",
                    autocomplete: false,
                    chkPass: true
                },
                password_confirm: {
                    label: 'Confirm Password',
                    type: 'sensitive',
                    hasShowInputButton: true,
                    ngShow: 'ldap_user == false && socialAuthUser === false',
                    addRequired: true,
                    editRequired: false,
                    awPassMatch: true,
                    associated: 'password',
                    autocomplete: false
                },
                user_type: {
                    label: 'User Type',
                    type: 'select',
                    ngOptions: 'item as item.label for item in user_type_options track by item.type',
                    disableChooseOption: true,
                    ngModel: 'user_type',
                    ngShow: 'current_user["is_superuser"]',
                },
            },

            buttons: {
                cancel: {
                    ngClick: 'formCancel()'
                },
                save: {
                    ngClick: 'formSave()',
                    ngDisabled: true
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
                    title: 'Permissions',
                    iterator: 'permission',
                    open: false,
                    index: false,
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
                            awToolTip: 'Dissasociate permission from user'
                        }
                    },
                    hideOnSuperuser: true
                }
            }

        });
