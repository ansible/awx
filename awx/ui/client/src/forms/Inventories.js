/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name forms.function:Inventories
 * @description This form is for adding/editing an inventory
 */

export default
angular.module('InventoryFormDefinition', ['ScanJobsListDefinition'])
    .factory('InventoryFormObject', ['i18n', function(i18n) {
        return {

        addTitle: i18n._('New Inventory'),
        editTitle: '{{ inventory_name }}',
        name: 'inventory',
        basePath: 'inventory',
        // the top-most node of this generated state tree
        stateTree: 'inventories',
        tabs: true,

        fields: {
            inventory_name: {
                realName: 'name',
                label: i18n._('Name'),
                type: 'text',
                required: true,
                capitalize: false,
                ngDisabled: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            inventory_description: {
                realName: 'description',
                label: i18n._('Description'),
                type: 'text',
                ngDisabled: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            organization: {
                label: i18n._('Organization'),
                type: 'lookup',
                basePath: 'organizations',
                list: 'OrganizationList',
                sourceModel: 'organization',
                sourceField: 'name',
                awRequiredWhen: {
                    reqExpression: "organizationrequired",
                    init: "true"
                },
                ngDisabled: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            variables: {
                label: i18n._('Variables'),
                type: 'textarea',
                class: 'Form-formGroup--fullWidth',
                rows: 6,
                "default": "---",
                awPopOver: "<p>" + i18n._("Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>' + i18n.sprintf(i18n._('View JSON examples at %s'), '<a href="http://www.json.org" target="_blank">www.json.org</a>') + '</p>' +
                    '<p>' + i18n.sprintf(i18n._('View YAML examples at %s'), '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a>') + '</p>',
                dataTitle: i18n._('Inventory Variables'),
                dataPlacement: 'right',
                dataContainer: 'body',
                ngDisabled: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd)' // TODO: get working
            }
        },

        buttons: {
            cancel: {
                ngClick: 'formCancel()',
                ngShow: '(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            close: {
                ngClick: 'formCancel()',
                ngHide: '(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            save: {
                ngClick: 'formSave()',
                ngDisabled: true,
                ngShow: '(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            }
        },
        related: {
            permissions: {
                awToolTip: i18n._('Please save before assigning permissions'),
                dataPlacement: 'top',
                basePath: 'api/v1/inventories/{{$stateParams.inventory_id}}/access_list/',
                type: 'collection',
                title: 'Permissions',
                iterator: 'permission',
                index: false,
                open: false,
                search: {
                    order_by: 'username'
                },
                actions: {
                    add: {
                        label: i18n._('Add'),
                        ngClick: "$state.go('.add')",
                        awToolTip: 'Add a permission',
                        actionClass: 'btn List-buttonSubmit',
                        buttonContent: '&#43; ADD',
                        ngShow: '(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'

                    }
                },
                fields: {
                    username: {
                        label: i18n._('User'),
                        linkBase: 'users',
                        class: 'col-lg-3 col-md-3 col-sm-3 col-xs-4'
                    },
                    role: {
                        label: i18n._('Role'),
                        type: 'role',
                        noSort: true,
                        class: 'col-lg-4 col-md-4 col-sm-4 col-xs-4',
                    },
                    team_roles: {
                        label: i18n._('Team Roles'),
                        type: 'team_roles',
                        noSort: true,
                        class: 'col-lg-5 col-md-5 col-sm-5 col-xs-4',
                    }
                }
            }
        },

        relatedSets: function() {
            return {
                permissions: {
                    awToolTip: i18n._('Please save before assigning permissions'),
                    dataPlacement: 'top',
                    basePath: 'inventories/:id/access_list/',
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
                            buttonContent: '&#43; ' + i18n._('ADD'),
                            ngShow: '(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
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
                            noSearch: true
                        },
                        team_roles: {
                            label: i18n._('Team Roles'),
                            type: 'team_roles',
                            noSort: true,
                            class: 'col-lg-5 col-md-5 col-sm-5 col-xs-4',
                            noSearch: true
                        }
                    }
                }
            };
        }

        };}])

    .factory('InventoryForm', ['InventoryFormObject', 'ScanJobsList',
        function(InventoryFormObject, ScanJobsList) {
            return function() {
                var itm;
                for (itm in InventoryFormObject.related) {
                    if (InventoryFormObject.related[itm].include === "ScanJobsList") {
                        InventoryFormObject.related[itm] = ScanJobsList;
                        InventoryFormObject.related[itm].generateList = true; // tell form generator to call list generator and inject a list
                    }
                }
                return InventoryFormObject;
            };
        }
    ]);
