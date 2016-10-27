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

export default
    angular.module('TeamFormDefinition', [])
        .factory('TeamForm', ['i18n', function(i18n) {
        return {

            addTitle: i18n._('New Team'), //Legend in add mode
            editTitle: '{{ name }}', //Legend in edit mode
            name: 'team',
            tabs: true,

            fields: {
                name: {
                    label: i18n._('Name'),
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: false,
                    ngDisabled: '!(team_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                description: {
                    label: i18n._('Description'),
                    type: 'text',
                    addRequired: false,
                    editRequired: false,
                    ngDisabled: '!(team_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                organization: {
                    label: i18n._('Organization'),
                    type: 'lookup',
                    sourceModel: 'organization',
                    sourceField: 'name',
                    addRequired: true,
                    editRequire: false,
                    ngClick: 'lookUpOrganization()',
                    awRequiredWhen: {
                        reqExpression: "orgrequired",
                        init: true
                    },
                    ngDisabled: '!(team_obj.summary_fields.user_capabilities.edit || canAdd)'
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
                access_list: {
                    dataPlacement: 'top',
                    awToolTip: i18n._('Please save before adding users'),
                    basePath: 'teams/:id/access_list/',
                    type: 'collection',
                    title: i18n._('Users'),
                    iterator: 'permission',
                    index: false,
                    open: false,
                    searchType: 'select',
                    actions: {
                        add: {
                            ngClick: "addPermissionWithoutTeamTab",
                            label: 'Add',
                            awToolTip: i18n._('Add user to team'),
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: i18n._('&#43; ADD'),
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
                            noSort: true,
                            class: 'col-lg-4 col-md-4 col-sm-4 col-xs-4',
                            searchable: false
                        }
                    }
                },
                roles: {
                    hideSearchAndActions: true,
                    dataPlacement: 'top',
                    awToolTip: i18n._('Please save before assigning permissions'),
                    basePath: 'teams/:id/roles/',
                    type: 'collection',
                    title: i18n._('Granted Permissions'),
                    iterator: 'role',
                    open: false,
                    index: false,
                    actions: {},
                    emptyListText: i18n._('No permissions have been granted'),
                    fields: {
                        name: {
                            label: i18n._('Name'),
                            ngBind: 'role.summary_fields.resource_name',
                            linkTo: '{{convertApiUrl(role.related[role.summary_fields.resource_type])}}',
                            noSort: true
                        },
                        type: {
                            label: i18n._('Type'),
                            ngBind: 'role.summary_fields.resource_type_display_name',
                            noSort: true
                        },
                        role: {
                            label: i18n._('Role'),
                            ngBind: 'role.name',
                            noSort: true
                        }
                    },
                    fieldActions: {
                        "delete": {
                            label: i18n._('Remove'),
                            ngClick: 'deletePermissionFromTeam(team_id, team_obj.name, role.name, role.summary_fields.resource_name, role.related.teams)',
                            'class': "List-actionButton--delete",
                            iconClass: 'fa fa-times',
                            awToolTip: i18n._('Dissasociate permission from team'),
                            dataPlacement: 'top',
                            ngShow: 'permission.summary_fields.user_capabilities.unattach'
                        }
                    },
                    hideOnSuperuser: true
                }
            },
        };}]); //InventoryForm
