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

export default ['i18n', function(i18n) {
        return {

            addTitle: i18n._('NEW USER'),
            editTitle: '{{ username }}',
            name: 'user',
            // the top-most node of generated state tree
            stateTree: 'users',
            forceListeners: true,
            tabs: true,
            messageBar: {
                ngShow: 'isOrgAdmin && !canEdit',
                message: i18n._("Contact your System Administrator to grant you the appropriate permissions to add and edit Users and Teams.")
            },
            fields: {
                first_name: {
                    label: i18n._('First Name'),
                    type: 'text',
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)',
                    required: false,
                },
                last_name: {
                    label: i18n._('Last Name'),
                    type: 'text',
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)',
                    required: false,
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
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                email: {
                    label: i18n._('Email'),
                    type: 'email',
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)',
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
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                password: {
                    label: i18n._('Password'),
                    type: 'sensitive',
                    hasShowInputButton: true,
                    ngShow: 'ldap_user == false && socialAuthUser === false && external_account === null',
                    awRequiredWhen: {
                        reqExpression: "isAddForm",
                        init: false
                    },
                    ngChange: "clearPWConfirm()",
                    autocomplete: false,
                    ngDisabled: '!(user_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                password_confirm: {
                    label: i18n._('Confirm Password'),
                    type: 'sensitive',
                    hasShowInputButton: true,
                    ngShow: 'ldap_user == false && socialAuthUser === false && external_account === null',
                    awRequiredWhen: {
                        reqExpression: "isAddForm",
                        init: false
                    },
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
                    name: 'organizations',
                    awToolTip: i18n._('Please save before assigning to organizations.'),
                    basePath: 'api/v2/users/{{$stateParams.user_id}}/organizations',
                    emptyListText: i18n._('Please add user to an Organization.'),
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
                            label: i18n._('Name'),
                            columnClass: "col-sm-6"
                        },
                        description: {
                            label: i18n._('Description'),
                            columnClass: "col-sm-6"
                        }
                    },
                    //hideOnSuperuser: true // RBAC defunct
                },
                teams: {
                    name: 'teams',
                    awToolTip: i18n._('Please save before assigning to teams.'),
                    basePath: 'api/v2/users/{{$stateParams.user_id}}/teams',
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
                    emptyListText: i18n._('This user is not a member of any teams'),
                    fields: {
                        name: {
                            key: true,
                            label: i18n._('Name'),
                            columnClass: "col-sm-6"
                        },
                        description: {
                            label: i18n._('Description'),
                            columnClass: "col-sm-6"
                        }
                    },
                    //hideOnSuperuser: true // RBAC defunct
                },
                permissions: {
                    name: 'permissions',
                    basePath: 'api/v2/users/{{$stateParams.user_id}}/roles/',
                    search: {
                        page_size: '10',
                        order_by: 'id'
                    },
                    awToolTip: i18n._('Please save before assigning to organizations.'),
                    dataPlacement: 'top',
                    hideSearchAndActions: true,
                    type: 'collection',
                    title: i18n._('Permissions'),
                    iterator: 'permission',
                    open: false,
                    index: false,
                    emptyListText: i18n._('No permissions have been granted'),
                    fields: {
                        name: {
                            label: i18n._('Name'),
                            ngBind: 'permission.summary_fields.resource_name',
                            ngClick: "redirectToResource(permission)",
                            nosort: true,
                            columnClass: "col-sm-4"
                        },
                        type: {
                            label: i18n._('Type'),
                            ngBind: 'permission.summary_fields.resource_type_display_name',
                            nosort: true,
                            columnClass: "col-sm-3"
                        },
                        role: {
                            label: i18n._('Role'),
                            ngBind: 'permission.name',
                            nosort: true,
                            columnClass: "col-sm-3"
                        },
                    },
                    actions: {
                        add: {
                            ngClick: "$state.go('.add')",
                            label: i18n._('Add'),
                            awToolTip: i18n._('Grant Permission'),
                            actionClass: 'at-Button--add',
                            actionId: 'button-add--permission',
                            ngShow: '(!is_superuser && (user_obj.summary_fields.user_capabilities.edit || canAdd))'
                        }
                    },
                    fieldActions: {
                        columnClass: 'col-sm-2',
                        "delete": {
                            label: i18n._('Remove'),
                            ngClick: 'deletePermissionFromUser(user_id, username, permission.name, permission.summary_fields.resource_name, permission.related.users)',
                            iconClass: 'fa fa-times',
                            awToolTip: i18n._('Dissassociate permission from user'),
                            ngShow: 'permission.summary_fields.user_capabilities.unattach'
                        }
                    },
                    //hideOnSuperuser: true // RBAC defunct
                },
                tokens: {
                    ngIf: 'isCurrentlyLoggedInUser',
                    title: i18n._('Tokens'),
                    skipGenerator: true,
                }
            }

        };}];
