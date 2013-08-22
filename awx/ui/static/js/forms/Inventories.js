/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Inventories.js
 *  Form definition for User model
 *
 * 
 */
angular.module('InventoryFormDefinition', [])
    .value(
    'InventoryForm', {
        
        addTitle: 'Create Inventory',
        editTitle: '{{ inventory_name }}',
        name: 'inventory',
        parseTypeName: 'inventoryParseType',
        well: true,
        /*,
        formLabelSize: 'col-lg-3',
        formFieldSize: 'col-lg-9',*/

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
                addRequired: true,
                editRequired: true,
                ngClick: 'lookUpOrganization()',
                awRequiredWhen: {variable: "organizationrequired", init: "true" }
                },
            inventory_variables: {
                realName: 'variables',
                label: 'Variables',
                type: 'textarea',
                'class': 'span12',
                addRequired: false,
                editRequird: false, 
                rows: 10,
                "default": "---",
                awPopOver: "<p>Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    '<p>View YAML examples at <a href="http://www.ansibleworks.com/docs/YAMLSyntax.html" target="_blank">ansibleworks.com</a></p>',
                dataTitle: 'Inventory Variables',
                dataPlacement: 'bottom',
                dataContainer: '#form-modal .modal-content'
                }
            },

        buttons: { //for now always generates <button> tags 
            save: { 
                label: 'Save', 
                icon: 'icon-ok',
                "class": 'btn-success',
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                label: 'Reset',
                icon: 'icon-trash',
                'class': 'btn btn-default',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: {

            groups: {
                type: 'tree',
                open: true,
                actions: { 
                    }
                },

            hosts: {
                type: 'treeview',
                title: "groupTitle",
                iterator: 'host',
                
                actions: {
                    },
                
                fields: {
                    name: {
                        key: true,
                        label: 'Host Name',
                        ngClick: "editHost(\{\{ host.id \}\}, '\{\{ host.name \}\}')",
                        badgeShow: "\{\{ host.has_active_failures \}\}",
                        badgeIcon: 'icon-exclamation-sign',
                        badgeToolTip: 'Most recent job failed',
                        badgePlacement: 'bottom',
                        columnClass: 'col-lg-3'
                        },
                    groups: {
                        label: 'Groups',
                        searchable: false,
                        sourceModel: 'groups',
                        sourceField: 'name',
                        nosort: true
                        },
                    dropdown: {
                        type: 'DropDown',
                        label: 'View',
                        ngDisabled: 'host.last_job == null',
                        options: [
                            { ngClick: 'viewJobs(\{\{ host.id \}\})', label: 'Jobs' },
                            { ngClick: "viewLastEvents(\{\{ host.id \}\}, '\{\{ host.last_job \}\}', '\{\{ host.name \}\}', " +
                                "'\{\{ host.summary_fields.last_job.name \}\}')", label: 'Latest job events' },
                            { ngClick: "viewLastSummary(\{\{ host.id \}\}, '\{\{ host.last_job \}\}', '\{\{ host.name \}\}', " +
                                "'\{\{ host.summary_fields.last_job.name \}\}')", label: 'Latest host summary' }
                            ]
                        }
                    },
                fieldActions: {
                    }
                }
            }

    }); //InventoryForm

