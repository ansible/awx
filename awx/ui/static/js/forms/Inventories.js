/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Inventories.js
 *  Form definition for User model
 *
 *
 */
 /**
 * @ngdoc function
 * @name forms.function:Inventories
 * @description This form is for adding/editing an inventory
*/

export default
    angular.module('InventoryFormDefinition', ['ScanJobsListDefinition'])
        .value('InventoryFormObject', {

            addTitle: 'Create Inventory',
            editTitle: '{{ inventory_name }}',
            name: 'inventory',
            well: true,
            collapse: true,
            collapseTitle: "Properties",
            collapseMode: 'edit',
            collapseOpen: true,

            actions: {
                stream: {
                    'class': "btn-primary btn-xs activity-btn",
                    ngClick: "showActivity()",
                    awToolTip: "View Activity Stream",
                    dataPlacement: "top",
                    icon: "icon-comments-alt",
                    mode: 'edit',
                    iconSize: 'large'
                }
            },

            fields: {
                inventory_name: {
                    realName: 'name',
                    label: 'Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    capitalize: false
                },
                inventory_description: {
                    realName: 'description',
                    label: 'Description',
                    type: 'text',
                    addRequired: false,
                    editRequired: false
                },
                organization: {
                    label: 'Organization',
                    type: 'lookup',
                    sourceModel: 'organization',
                    sourceField: 'name',
                    ngClick: 'lookUpOrganization()',
                    awRequiredWhen: {
                        variable: "organizationrequired",
                        init: "true"
                    }
                },
                variables: {
                    label: 'Variables',
                    type: 'textarea',
                    'class': 'span12',
                    addRequired: false,
                    editRequird: false,
                    rows: 6,
                    "default": "---",
                    awPopOver: "<p>Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                        "JSON:<br />\n" +
                        "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
                        "YAML:<br />\n" +
                        "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                        '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                        '<p>View YAML examples at <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                    dataTitle: 'Inventory Variables',
                    dataPlacement: 'right',
                    dataContainer: 'body'
                }
            },

            buttons: {
                save: {
                    ngClick: 'formSave()',
                    ngDisabled: true
                },
                reset: {
                    ngClick: 'formReset()',
                    ngDisabled: true
                }
            },

            related: {
                scan_jobs: {
                    type: 'collection',
                    title: 'Scan Jobs',
                    iterator: 'scan_job',
                    index: false,
                    open: false,

                    actions: {
                        add: {
                            ngClick: "addScanJob(inventory_id)",
                            icon: 'icon-plus',
                            label: 'Add',
                            awToolTip: 'Add a scan job'
                        }
                    },

                    fields: {
                        name: {
                            key: true,
                            label: 'Name'
                        },
                        description: {
                            label: 'Description'
                        }
                    },

                    fieldActions: {
                        edit: {
                            label: 'Edit',
                            ngClick: "edit('organizations', organization.id, organization.name)",
                            icon: 'icon-edit',
                            awToolTip: 'Edit the organization',
                            'class': 'btn btn-default'
                        },
                        "delete": {
                            label: 'Delete',
                            ngClick: "delete('organizations', organization.id, organization.name, 'organizations')",
                            icon: 'icon-trash',
                            "class": 'btn-danger',
                            awToolTip: 'Delete the organization'
                        }
                    }
                }
            },

            relatedSets: function(urls) {
                return {
                    scan_jobs: {
                        iterator: 'scan_job',
                        url: urls.organizations
                    },
                    // schedules: {
                    //     iterator: 'schedule',
                    //     url: urls.schedules
                    // }
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
