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
        .value('TeamForm', {

            addTitle: 'New Team', //Legend in add mode
            editTitle: '{{ name }}', //Legend in edit mode
            name: 'team',
            tabs: true,

            fields: {
                name: {
                    label: 'Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: false,
                    ngDisabled: '!canEdit'
                },
                description: {
                    label: 'Description',
                    type: 'text',
                    addRequired: false,
                    editRequired: false,
                    ngDisabled: '!canEdit'
                },
                organization: {
                    label: 'Organization',
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
                    ngDisabled: '!canEdit'
                }
            },

            buttons: {
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: 'canEdit'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!canEdit'
                },
                save: {
                    ngClick: 'formSave()',
                    ngDisabled: true,
                    ngShow: 'canEdit'
                }
            },

            related: {
                access_list: {
                    dataPlacement: 'top',
                    awToolTip: 'Please save before adding users',
                    basePath: 'teams/:id/access_list/',
                    type: 'collection',
                    title: 'Users',
                    iterator: 'permission',
                    index: false,
                    open: false,
                    searchType: 'select',
                    actions: {
                        add: {
                            ngClick: "addPermissionWithoutTeamTab",
                            label: 'Add',
                            awToolTip: 'Add user to team',
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ADD',
                            ngShow: 'canEdit'
                        }
                    },

                    fields: {
                        username: {
                            key: true,
                            label: 'User',
                            linkBase: 'users',
                            class: 'col-lg-3 col-md-3 col-sm-3 col-xs-4'
                        },
                        role: {
                            label: 'Role',
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
                    awToolTip: 'Please save before assigning permissions',
                    basePath: 'teams/:id/roles/',
                    type: 'collection',
                    title: 'Granted Permissions',
                    iterator: 'role',
                    open: false,
                    index: false,
                    actions: {},
                    emptyListText: 'No permissions have been granted',
                    fields: {
                        name: {
                            label: 'Name',
                            ngBind: 'role.summary_fields.resource_name',
                            linkTo: '{{convertApiUrl(role.related[role.summary_fields.resource_type])}}',
                            noSort: true
                        },
                        type: {
                            label: 'Type',
                            ngBind: 'role.summary_fields.resource_type_display_name',
                            noSort: true
                        },
                        role: {
                            label: 'Role',
                            ngBind: 'role.name',
                            noSort: true
                        }
                    },
                    fieldActions: {
                        "delete": {
                            label: 'Remove',
                            ngClick: 'deletePermissionFromTeam(team_id, team_obj.name, role.name, role.summary_fields.resource_name, role.related.teams)',
                            'class': "List-actionButton--delete",
                            iconClass: 'fa fa-times',
                            awToolTip: 'Dissasociate permission from team',
                            dataPlacement: 'top'
                        }
                    },
                    hideOnSuperuser: true
                }
            },
        }); //InventoryForm
