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
        .value('InventoryFormObject', {

            addTitle: 'New Inventory',
            editTitle: '{{ inventory_name }}',
            name: 'inventory',
            tabs: true,

            fields: {
                inventory_name: {
                    realName: 'name',
                    label: 'Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: false,
                    ngDisabled: '!inventory_obj.summary_fields.user_capabilities.edit'
                },
                inventory_description: {
                    realName: 'description',
                    label: 'Description',
                    type: 'text',
                    addRequired: false,
                    editRequired: false,
                    ngDisabled: '!inventory_obj.summary_fields.user_capabilities.edit'
                },
                organization: {
                    label: 'Organization',
                    type: 'lookup',
                    sourceModel: 'organization',
                    sourceField: 'name',
                    ngClick: 'lookUpOrganization()',
                    awRequiredWhen: {
                        reqExpression: "organizationrequired",
                        init: "true"
                    },
                    ngDisabled: '!inventory_obj.summary_fields.user_capabilities.edit'
                },
                variables: {
                    label: 'Variables',
                    type: 'textarea',
                    class: 'Form-formGroup--fullWidth',
                    addRequired: false,
                    editRequird: false,
                    rows: 6,
                    "default": "---",
                    awPopOver: "<p>Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                        "JSON:<br />\n" +
                        "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                        "YAML:<br />\n" +
                        "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                        '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                        '<p>View YAML examples at <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                    dataTitle: 'Inventory Variables',
                    dataPlacement: 'right',
                    dataContainer: 'body',
                    ngDisabled: '!inventory_obj.summary_fields.user_capabilities.edit' // TODO: get working
                }
            },

            buttons: {
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: 'inventory_obj.summary_fields.user_capabilities.edit'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngHide: 'inventory_obj.summary_fields.user_capabilities.edit'
                },
                save: {
                    ngClick: 'formSave()',
                    ngDisabled: true,
                    ngShow: 'inventory_obj.summary_fields.user_capabilities.edit'
                }
            },

            related: {
                permissions: {
                    awToolTip: 'Please save before assigning permissions',
                    dataPlacement: 'top',
                    basePath: 'inventories/:id/access_list/',
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
                            ngShow: 'inventory_obj.summary_fields.user_capabilities.edit'
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
                            noSearch: true
                        },
                        team_roles: {
                            label: 'Team Roles',
                            type: 'team_roles',
                            noSort: true,
                            class: 'col-lg-5 col-md-5 col-sm-5 col-xs-4',
                            noSearch: true
                        }
                    }
                }
            },

            relatedSets: function(urls) {
                return {
                    permissions: {
                        iterator: 'permission',
                        url: urls.access_list
                    }
                };
            }

        })
        .factory('InventoryForm', ['InventoryFormObject', 'ScanJobsList',
        function(InventoryFormObject, ScanJobsList) {
            return function() {
                var itm;
                for (itm in InventoryFormObject.related) {
                    if (InventoryFormObject.related[itm].include === "ScanJobsList") {
                      InventoryFormObject.related[itm] = ScanJobsList;
                      InventoryFormObject.related[itm].generateList = true;   // tell form generator to call list generator and inject a list
                    }
                }
                return InventoryFormObject;
            };
        }]);
