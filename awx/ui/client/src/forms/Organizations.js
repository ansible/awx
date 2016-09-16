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
        .value('OrganizationFormObject', {

            addTitle: 'New Organization', //Title in add mode
            editTitle: '{{ name }}', //Title in edit mode
            name: 'organization', //entity or model name in singular form
            tabs: true,

            fields: {
                name: {
                    label: 'Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: false,
                    ngDisabled: '!(organization_obj.summary_fields.user_capabilities.edit || canAdd)'
                },
                description: {
                    label: 'Description',
                    type: 'text',
                    addRequired: false,
                    editRequired: false,
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
                    basePath: 'organizations/:id/access_list/',
                    awToolTip: 'Please save before assigning permissions',
                    dataPlacement: 'top',
                    type: 'collection',
                    title: 'Permissions',
                    iterator: 'permission',
                    index: false,
                    open: false,
                    searchType: 'select',
                    actions: {
                        add: {
                            ngClick: "addPermission",
                            label: 'Add',
                            awToolTip: 'Add a permission',
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ADD',
                            ngShow: '(organization_obj.summary_fields.user_capabilities.edit || canAdd)'
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
                        },
                        team_roles: {
                            label: 'Team Roles',
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
        })

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
