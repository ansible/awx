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
            // the top-most node of generated state tree
            stateTree: 'users',
            forceListeners: true,
            tabs: true,

            fields: {
                first_name: {
                    label: i18n._('First Name'),
                    type: 'text',
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || !canAdd)',
                    required: true,
                    capitalize: true
                },
                last_name: {
                    label: i18n._('Last Name'),
                    type: 'text',
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || !canAdd)',
                    required: true,
                    capitalize: true
                },
                email: {
                    label: i18n._('Email'),
                    type: 'email',
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || !canAdd)',
                    required: true,
                    autocomplete: false
                },
                username: {
                    label: i18n._('Username'),
                    type: 'text',
                    awRequiredWhen: {
                        reqExpression: "not_ldap_user && external_account === null",
                        init: true
                    },
                    autocomplete: false,
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || !canAdd)'
                },
                organization: {
                    label: i18n._('Organization'),
                    type: 'lookup',
                    list: 'OrganizationList',
                    basePath: 'organizations',
                    sourceModel: 'organization',
                    sourceField: 'name',
                    required: true,
                    excludeMode: 'edit',
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || !canAdd)'
                },
                password: {
                    label: i18n._('Password'),
                    type: 'sensitive',
                    hasShowInputButton: true,
                    ngShow: 'ldap_user == false && socialAuthUser === false && external_account === null',
                    ngRequired: "$state.match('add')",
                    labelNGClass: "{'prepend-asterisk' : $state.matches('add')}",
                    ngChange: "clearPWConfirm('password_confirm')",
                    autocomplete: false,
                    chkPass: true,
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || !canAdd)'
                },
                password_confirm: {
                    label: i18n._('Confirm Password'),
                    type: 'sensitive',
                    hasShowInputButton: true,
                    ngShow: 'ldap_user == false && socialAuthUser === false && external_account === null',
                    ngRequired: "$state.match('add')",
                    labelNGClass: "{'prepend-asterisk' : $state.matches('add')}",
                    awPassMatch: true,
                    associated: 'password',
                    autocomplete: false,
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || !canAdd)'
                },
                user_type: {
                    label: i18n._('User Type'),
                    type: 'select',
                    ngOptions: 'item as item.label for item in user_type_options track by item.type',
                    disableChooseOption: true,
                    ngModel: 'user_type',
                    ngShow: 'current_user["is_superuser"]',
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || !canAdd)'
                },
            },

            buttons: {
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: '(user_obj.summary_fields.user_capabilities.edit || !canAdd)'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!(user_obj.summary_fields.user_capabilities.edit || !canAdd)'
                },
                save: {
                    ngClick: 'formSave()',
                    ngDisabled: true,
                    ngShow: '(user_obj.summary_fields.user_capabilities.edit || !canAdd)'
                }
            },

            related: {
                organizations: {
                    awToolTip: i18n._('Please save before assigning to organizations'),
                    basePath: 'api/v1/users/{{$stateParams.user_id}}/organizations',
                    search: {
                        page_size: '10'
                    },
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
                    //hideOnSuperuser: true // RBAC defunct
                },
                teams: {
                    awToolTip: i18n._('Please save before assigning to teams'),
                    basePath: 'api/v1/users/{{$stateParams.user_id}}/teams',
                    search: {
                        page_size: '10'
                    },
                    dataPlacement: 'top',
                    type: 'collection',
                    title: i18n._('Teams'),
                    iterator: 'team',
                    open: false,
                    index: false,
                    actions: {},
                    emptyListText: 'This user is not a member of any teams',
                    fields: {
                        name: {
                            key: true,
                            label: 'Name'
                        },
                        description: {
                            label: 'Description'
                        }
                    },
                    //hideOnSuperuser: true // RBAC defunct
                },
                permissions: {
                    basePath: 'api/v1/users/{{$stateParams.user_id}}/roles/',
                    search: {
                        page_size: '10',
                        // @todo ask about name field / serializer on this endpoint
                        order_by: 'id'
                    },
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
                    // @issue https://github.com/ansible/ansible-tower/issues/3487
                    // actions: {
                    //     add: {

                    //     }
                    // }
                    fieldActions: {
                        "delete": {
                            label: i18n._('Remove'),
                            ngClick: 'deletePermissionFromUser(user_id, username, permission.name, permission.summary_fields.resource_name, permission.related.users)',
                            iconClass: 'fa fa-times',
                            awToolTip: i18n._('Dissasociate permission from user'),
                            ngShow: 'permission.summary_fields.user_capabilities.unattach'
                        }
                    },
                    //hideOnSuperuser: true // RBAC defunct
                }
            }

        };}]);
