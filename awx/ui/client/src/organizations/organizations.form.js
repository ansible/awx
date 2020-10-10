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
                    control: '<instance-groups-multiselect instance-groups="instance_groups" field-is-disabled="!(organization_obj.summary_fields.user_capabilities.edit || canAdd) || (!current_user.is_superuser && isOrgAdmin)"></instance-groups-multiselect>',
                },
                custom_virtualenv: {
                    label: i18n._('Ansible Environment'),
                    defaultText: i18n._('Use Default Environment'),
                    type: 'select',
                    ngOptions: 'venv for venv in custom_virtualenvs_options track by venv',
                    awPopOver: "<p>" + i18n._("Select the custom Python virtual environment for this organization to run on.") + "</p>",
                    dataTitle: i18n._('Ansible Environment'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    ngDisabled: '!(organization_obj.summary_fields.user_capabilities.edit || canAdd)',
                    ngShow: 'custom_virtualenvs_visible'
                },
                credential: {
                    label: i18n._('Galaxy Credentials'),
                    type: 'custom',
                    awPopOver: "<p>" + i18n._("Select Galaxy credentials. The selection order sets the order in which Tower will download roles/collections using `ansible-galaxy`.") + "</p>",
                    dataTitle: i18n._('Galaxy Credentials'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    control: '<galaxy-credentials-multiselect galaxy-credentials="credentials" field-is-disabled="!(organization_obj.summary_fields.user_capabilities.edit || canAdd) || (!current_user.is_superuser && isOrgAdmin)"></galaxy-credentials-multiselect>',
                },
                max_hosts: {
                    label: i18n._('Max Hosts'),
                    type: 'number',
                    integer: true,
                    min: 0,
                    max: 2147483647,
                    default: 0,
                    spinner: true,
                    dataTitle: i18n._('Max Hosts'),
                    dataPlacement: 'right',
                    dataContainer: 'body',
                    awPopOver: "<p>" + i18n._("The maximum number of hosts allowed to be managed by this organization. Value defaults to 0 which means no limit. Refer to the Ansible documentation for more details.") + "</p>",
                    ngDisabled: '!current_user.is_superuser',
                    ngShow: 'BRAND_NAME === "Tower"'
                },
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
                    basePath: 'api/v2/organizations/{{$stateParams.organization_id}}/users/',
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
                            actionClass: 'at-Button--add',
                            actionId: 'button-add',
                            ngShow: '(organization_obj.summary_fields.user_capabilities.edit || canAdd)'
                        }
                    },

                    fields: {
                        username: {
                            key: true,
                            label: i18n._('User'),
                            linkBase: 'users',
                            columnClass: 'col-sm-4'
                        },
                        first_name: {
                            label: i18n._('First name'),
                            columnClass: 'col-sm-4'
                        },
                        last_name: {
                            label: i18n._('Last name'),
                            columnClass: 'col-sm-4'
                        }
                    }
                },
                permissions: {
                    name: 'permissions',
                    awToolTip: i18n._('Please save before assigning permissions.'),
                    djangoModel: 'access_list',
                    dataPlacement: 'top',
                    basePath: 'api/v2/organizations/{{$stateParams.organization_id}}/access_list/',
                    search: {
                        order_by: 'username'
                    },
                    type: 'collection',
                    title: i18n._('Permissions'),
                    iterator: 'permission',
                    index: false,
                    open: false,
                    actions: {
                        add: {
                            ngClick: "$state.go('.add')",
                            label: i18n._('Add'),
                            awToolTip: i18n._('Add a permission'),
                            actionClass: 'at-Button--add',
                            actionId: 'button-add--permission',
                            ngShow: '(organization_obj.summary_fields.user_capabilities.edit || canAdd)'
                        }
                    },
                    fields: {
                        username: {
                            key: true,
                            label: i18n._('User'),
                            linkBase: 'users',
                            columnClass: 'col-lg-3 col-md-3 col-sm-3 col-xs-4'
                        },
                        role: {
                            label: i18n._('Role'),
                            type: 'role',
                            nosort: true,
                            columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-4',
                        },
                        team_roles: {
                            label: i18n._('Team Roles'),
                            type: 'team_roles',
                            nosort: true,
                            columnClass: 'col-lg-5 col-md-5 col-sm-5 col-xs-4',
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
