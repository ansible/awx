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
            messageBar: {
                ngShow: 'isOrgAdmin && !canEdit',
                message: i18n._("Contact your System Administrator to grant you the appropriate permissions to add and edit Users and Teams.")
            },
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
                            actionClass: 'at-Button--add',
                            actionId: 'button-add--user',
                            ngShow: '(team_obj.summary_fields.user_capabilities.edit || canAdd)'
                        }
                    },

                    fields: {
                        username: {
                            key: true,
                            label: i18n._('User'),
                            linkBase: 'users',
                            columnClass: 'col-sm-3'
                        },
                        first_name: {
                            label: i18n._('First Name'),
                            columnClass: 'col-sm-3'
                        },
                        last_name: {
                            label: i18n._('Last Name'),
                            columnClass: 'col-sm-3'
                        },
                        role: {
                            label: i18n._('Role'),
                            type: 'role',
                            nosort: true,
                            columnClass: 'col-sm-3'
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
                            nosort: true,
                            columnClass: 'col-sm-4'
                        },
                        type: {
                            label: i18n._('Type'),
                            ngBind: 'permission.summary_fields.resource_type_display_name',
                            nosort: true,
                            columnClass: 'col-sm-3'
                        },
                        role: {
                            label: i18n._('Role'),
                            ngBind: 'permission.name',
                            nosort: true,
                            columnClass: 'col-sm-3'
                        }
                    },
                    fieldActions: {
                        columnClass: 'col-sm-2',
                        "delete": {
                            label: i18n._('Remove'),
                            ngClick: 'deletePermissionFromTeam(team_id, team_obj.name, permission.name, permission.summary_fields.resource_name, permission.related.teams)',
                            'class': "List-actionButton--delete",
                            iconClass: 'fa fa-times',
                            awToolTip: i18n._('Dissassociate permission from team'),
                            dataPlacement: 'top',
                            ngShow: 'permission.summary_fields.user_capabilities.unattach'
                        }
                    },
                    actions: {
                        add: {
                            ngClick: "$state.go('.add')",
                            label: i18n._('Add'),
                            awToolTip: i18n._('Grant Permission'),
                            actionClass: 'at-Button--add',
                            actionId: 'button-add--permission',
                            ngShow: '(team_obj.summary_fields.user_capabilities.edit || canEditOrg)'
                        }
                    }
                }
            },
        };}];
