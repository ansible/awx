/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

  /**
 * @ngdoc function
 * @name forms.function:Teams
 * @description This form is for adding/editing teams
*/

export default ['i18n', function(i18n) {
        return {

            addTitle: i18n._('NEW TEAM'), //Legend in add mode
            editTitle: '{{ name }}', //Legend in edit mode
            name: 'team',
            // the top-most node of generated state tree
            stateTree: 'teams',
            tabs: true,

            fields: {
                name: {
                    label: i18n._('Name'),
                    type: 'text',
                    ngDisabled: '!(team_obj.summary_fields.user_capabilities.edit || canAdd)',
                    required: true,
                    capitalize: false
                },
                description: {
                    label: i18n._('Description'),
                    type: 'text',
                    ngDisabled: '!(team_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                organization: {
                    label: i18n._('Organization'),
                    type: 'lookup',
                    list: 'OrganizationList',
                    sourceModel: 'organization',
                    basePath: 'organizations',
                    sourceField: 'name',
                    ngDisabled: '!(team_obj.summary_fields.user_capabilities.edit || canAdd) || !canEditOrg',
                    awLookupWhen: '(team_obj.summary_fields.user_capabilities.edit || canAdd) && canEditOrg',
                    required: true,
                }
            },

            buttons: {
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: '(team_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!(team_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                save: {
                    ngClick: 'formSave()',
                    ngDisabled: true,
                    ngShow: '(team_obj.summary_fields.user_capabilities.edit || canAdd)'
                }
            },

            related: {
                users: {
                    name: 'users',
                    dataPlacement: 'top',
                    awToolTip: i18n._('Please save before adding users.'),
                    basePath: 'api/v2/teams/{{$stateParams.team_id}}/access_list/',
                    search: {
                        order_by: 'username'
                    },
                    type: 'collection',
                    title: i18n._('Users'),
                    iterator: 'user',
                    index: false,
                    open: false,
                    actions: {
                        add: {
                            ngClick: "$state.go('.add')",
                            label: i18n._('Add'),
                            awToolTip: i18n._('Add User'),
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ' + i18n._('ADD'),
                            ngShow: '(team_obj.summary_fields.user_capabilities.edit || canAdd)'
                        }
                    },

                    fields: {
                        username: {
                            key: true,
                            label: i18n._('User'),
                            linkBase: 'users',
                            class: 'col-lg-3 col-md-3 col-sm-3 col-xs-4'
                        },
                        role: {
                            label: i18n._('Role'),
                            type: 'role',
                            nosort: true,
                            class: 'col-lg-4 col-md-4 col-sm-4 col-xs-4'
                        }
                    }
                },
                permissions: {
                    name: 'permissions',
                    basePath: 'api/v2/teams/{{$stateParams.team_id}}/roles/',
                    search: {
                        page_size: '10',
                        // @todo ask about name field / serializer on this endpoint
                        order_by: 'id'
                    },
                    awToolTip: i18n._('Please save before assigning permissions.'),
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
                            nosort: true
                        },
                        type: {
                            label: i18n._('Type'),
                            ngBind: 'permission.summary_fields.resource_type_display_name',
                            nosort: true
                        },
                        role: {
                            label: i18n._('Role'),
                            ngBind: 'permission.name',
                            nosort: true
                        }
                    },
                    fieldActions: {
                        "delete": {
                            label: i18n._('Remove'),
                            ngClick: 'deletePermissionFromTeam(team_id, team_obj.name, permission.name, permission.summary_fields.resource_name, permission.related.teams)',
                            'class': "List-actionButton--delete",
                            iconClass: 'fa fa-times',
                            awToolTip: i18n._('Dissasociate permission from team'),
                            dataPlacement: 'top',
                            ngShow: 'permission.summary_fields.user_capabilities.unattach'
                        }
                    },
                    actions: {
                        add: {
                            ngClick: "$state.go('.add')",
                            label: 'Add',
                            awToolTip: i18n._('Grant Permission'),
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ' + i18n._('ADD PERMISSIONS'),
                            ngShow: '(team_obj.summary_fields.user_capabilities.edit || canAdd)'
                        }
                    }
                }
            },
        };}];
