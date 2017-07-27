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

export default ['NotificationsList', 'i18n',
    function(NotificationsList, i18n) {
    return function() {
        var OrganizationFormObject = {

            addTitle: i18n._('NEW ORGANIZATION'), //Title in add mode
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
                },
                instance_groups: {
                    label: i18n._('Instance Groups'),
                    type: 'custom',
                    awPopOver: "<p>" + i18n._("Select the Instance Groups for this Organization to run on.") + "</p>",
                    dataTitle: i18n._('Instance Groups'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    control: '<instance-groups-multiselect instance-groups="instance_groups" field-is-disabled="!(organization_obj.summary_fields.user_capabilities.edit || canAdd)"></instance-groups-multiselect>',
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
                users: {
                    name: 'users',
                    dataPlacement: 'top',
                    awToolTip: i18n._('Please save before adding users.'),
                    basePath: 'api/v2/organizations/{{$stateParams.organization_id}}/access_list/',
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
                            awToolTip: i18n._('Add Users to this organization.'),
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ' + i18n._('ADD'),
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
                            nosort: true,
                            class: 'col-lg-4 col-md-4 col-sm-4 col-xs-4'
                        }
                    }
                },
                "notifications": {
                    include: "NotificationsList"

                }

            }
        };

        var itm;
        for (itm in OrganizationFormObject.related) {
            if (OrganizationFormObject.related[itm].include === "NotificationsList") {
                OrganizationFormObject.related[itm] = NotificationsList;
                OrganizationFormObject.related[itm].generateList = true;   // tell form generator to call list generator and inject a list
            }
        }
        return OrganizationFormObject;
    };
}];
