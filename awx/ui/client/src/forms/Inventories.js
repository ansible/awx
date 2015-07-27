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
                    awFeature: 'activity_streams',
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
                scan_job_templates: {
                    type: 'collection',
                    title: 'Scan Job Templates',
                    iterator: 'scan_job_template',
                    index: false,
                    open: false,

                    actions: {
                        add: {
                            ngClick: "addScanJob()",
                            icon: 'icon-plus',
                            label: 'Add',
                            awToolTip: 'Add a scan job template'
                        }
                    },

                    fields: {
                      smart_status: {
                          label: 'Status',
                          // columnClass: 'col-md-2 col-sm-2 col-xs-2',
                          searchable: false,
                          nosort: true,
                          ngInclude: "'/static/partials/scan-job-template-smart-status.html'",
                          type: 'template'
                        },
                        name: {
                            key: true,
                            label: 'Name',
                            linkTo: '/#/inventories/{{inventory_id}}/job_templates/{{scan_job_template.id}}'
                        },
                        description: {
                            label: 'Description'
                        }
                    },

                    fieldActions: {
                        submit: {
                          label: 'Launch',
                          ngClick: "launchScanJob()",
                          awToolTip: 'Launch the scan job template',
                          'class': 'btn btn-default'
                        },
                        schedule: {
                            label: 'Schedule',
                            ngClick: 'scheduleScanJob()',
                            awToolTip: 'Schedule future job template runs',
                            dataPlacement: 'top',
                        },
                        edit: {
                            label: 'Edit',
                            ngClick: "editScanJob()",
                            icon: 'icon-edit',
                            awToolTip: 'Edit the scan job template',
                            'class': 'btn btn-default'
                        },
                        "delete": {
                            label: 'Delete',
                            ngClick: "deleteScanJob()",
                            icon: 'icon-trash',
                            "class": 'btn-danger',
                            awToolTip: 'Delete the scan job template'
                        },
                        copy: {
                            label: 'Copy',
                            ngClick: "copyScanJobTemplate()",
                            "class": 'btn-danger btn-xs',
                            awToolTip: 'Copy template',
                            dataPlacement: 'top',
                            ngHide: 'job_template.summary_fields.can_copy === false'
                        }
                    }
                }
            },

            relatedSets: function(urls) {
                return {
                    scan_job_templates: {
                        iterator: 'scan_job_template',
                        url: urls.scan_job_templates
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
