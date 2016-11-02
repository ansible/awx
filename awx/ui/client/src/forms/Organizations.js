/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:Organizations
 * @description This form is for adding/editing an organization
*/

export default
    angular.module('OrganizationFormDefinition', [])
        .factory('OrganizationFormObject', ['i18n', function(i18n) {
        return {

            addTitle: i18n._('New Organization'), //Title in add mode
            editTitle: '{{ name }}', //Title in edit mode
            name: 'organization', //entity or model name in singular form
            stateTree: 'organizations',
            tabs: true,

            fields: {
                name: {
                    label: i18n._('Name'),
                    type: 'text',
                    ngDisabled: '!(organization_obj.summary_fields.user_capabilities.edit || canAdd)',
                    required: true,
                    capitalize: false
                },
                description: {
                    label: i18n._('Description'),
                    type: 'text',
                    ngDisabled: '!(organization_obj.summary_fields.user_capabilities.edit || canAdd)'
                }
            },

            buttons: { //for now always generates <button> tags
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: '(organization_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!(organization_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                save: {
                    ngClick: 'formSave()', //$scope.function to call on click, optional
                    ngDisabled: true,
                    ngShow: '(organization_obj.summary_fields.user_capabilities.edit || canAdd)'
                }
            },

            related: {
                permissions: {
                    awToolTip: i18n._('Please save before assigning permissions'),
                    basePath: 'api/v1/organizations/{{$stateParams.organization_id}}/access_list/',
                    search: {
                        order_by: 'username'
                    },
                    dataPlacement: 'top',
                    type: 'collection',
                    title: i18n._('Permissions'),
                    iterator: 'permission',
                    index: false,
                    open: false,
                    searchType: 'select',
                    actions: {
                        add: {
                            ngClick: "addPermission",
                            label: i18n._('Add'),
                            awToolTip: i18n._('Add a permission'),
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: i18n._('&#43; ADD'),
                            ngShow: '(organization_obj.summary_fields.user_capabilities.edit || canAdd)'
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
                        },
                        team_roles: {
                            label: i18n._('Team Roles'),
                            type: 'team_roles',
                            noSort: true,
                            class: 'col-lg-5 col-md-5 col-sm-5 col-xs-4',
                            searchable: false
                        }
                    }
                },
                "notifications": {
                    include: "NotificationsList"

                }

            },
            relatedSets: function(urls) {
                return {
                    permissions: {
                        iterator: 'permission',
                        url: urls.access_list
                    },
                    notifications: {
                        iterator: 'notification',
                        url: '/api/v1/notification_templates/'
                    }
                };
            }
        };}])

        .factory('OrganizationForm', ['OrganizationFormObject', 'NotificationsList',
            function(OrganizationFormObject, NotificationsList) {
            return function() {
                var itm;
                for (itm in OrganizationFormObject.related) {
                    if (OrganizationFormObject.related[itm].include === "NotificationsList") {
                        OrganizationFormObject.related[itm] = NotificationsList;
                        OrganizationFormObject.related[itm].generateList = true;   // tell form generator to call list generator and inject a list
                    }
                }
                return OrganizationFormObject;
            };
        }]);
